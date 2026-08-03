"""Paper generation tests with mocked OpenAI / R2."""

import pytest
from fastapi.testclient import TestClient

from app.services.papers import _target_paper_size


def _auth(monkeypatch: pytest.MonkeyPatch, uid: str = "user-paper-1") -> None:
    monkeypatch.setattr(
        "app.core.deps.verify_firebase_token",
        lambda _token: {"uid": uid, "phone_number": "+919700011122"},
    )


def test_target_paper_size_uses_ratio_with_min_and_safety_cap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.services.papers.settings.PAPER_MIN_QUESTIONS", 5)
    monkeypatch.setattr("app.services.papers.settings.PAPER_SIZE_RATIO", 0.3)
    monkeypatch.setattr("app.services.papers.settings.PAPER_MAX_QUESTIONS", 100)

    assert _target_paper_size(0) == 0
    # Small pool: floor(10*0.3)=3 → raise to MIN 5
    assert _target_paper_size(10) == 5
    # Mid pool: floor(40*0.3)=12 (no longer clipped by old max of 15)
    assert _target_paper_size(40) == 12
    # Large pool: floor(200*0.3)=60
    assert _target_paper_size(200) == 60
    # Safety ceiling still applies
    assert _target_paper_size(500) == 100
    # Never exceed available unique concepts
    assert _target_paper_size(3) == 3


def _fake_questions(specs: list[tuple[str, str, int, object | None]]):
    """(id, topic, ask_count, last_asked_at) → SimpleNamespace list."""
    from types import SimpleNamespace

    out = []
    for qid, topic, ask_count, last_asked in specs:
        out.append(
            SimpleNamespace(
                id=qid,
                variant_group_id=qid,
                topic=topic,
                ask_count=ask_count,
                last_asked_at=last_asked,
                stem=f"Stem {qid}",
            )
        )
    return out


def test_select_prefers_least_asked_and_shuffles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services import papers as papers_mod

    monkeypatch.setattr(papers_mod.settings, "PAPER_MIN_QUESTIONS", 3)
    monkeypatch.setattr(papers_mod.settings, "PAPER_SIZE_RATIO", 0.3)
    monkeypatch.setattr(papers_mod.settings, "PAPER_MAX_QUESTIONS", 100)
    monkeypatch.setattr(papers_mod, "_recent_paper_ids", lambda db, user_id: set())
    monkeypatch.setattr(
        papers_mod, "_question_ids_on_papers", lambda db, paper_ids: set()
    )
    # Keep presentation order stable for assertion
    monkeypatch.setattr(papers_mod.random, "shuffle", lambda _xs: None)
    monkeypatch.setattr(papers_mod.random, "random", lambda: 0.0)

    # 10 concepts → target max(3, floor(10*0.3)=3)=3
    candidates = _fake_questions(
        [
            ("q0", "A", 5, None),
            ("q1", "A", 0, None),
            ("q2", "A", 2, None),
            ("q3", "B", 0, None),
            ("q4", "B", 4, None),
            ("q5", "B", 1, None),
            ("q6", "C", 0, None),
            ("q7", "C", 3, None),
            ("q8", "C", 6, None),
            ("q9", "C", 7, None),
        ]
    )
    selected = papers_mod._select_questions_for_paper(
        db=None,
        candidates=candidates,
        user_id="u1",
    )
    assert len(selected) == 3
    # Least-asked (ask_count 0) must fill the paper before heavily used ones
    assert {q.id for q in selected} <= {"q1", "q3", "q6"}
    assert all(q.ask_count == 0 for q in selected)


def test_soft_cooldown_skips_recent_when_fresh_pool_is_enough(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from datetime import datetime, timezone
    from app.services import papers as papers_mod

    monkeypatch.setattr(papers_mod.settings, "PAPER_MIN_QUESTIONS", 2)
    monkeypatch.setattr(papers_mod.settings, "PAPER_SIZE_RATIO", 0.5)
    monkeypatch.setattr(papers_mod.settings, "PAPER_MAX_QUESTIONS", 100)
    monkeypatch.setattr(papers_mod.settings, "PAPER_COOLDOWN_DAYS", 14)
    monkeypatch.setattr(papers_mod, "_recent_paper_ids", lambda db, user_id: {"p1"})
    monkeypatch.setattr(
        papers_mod,
        "_question_ids_on_papers",
        lambda db, paper_ids: {"recent1", "recent2"},
    )
    monkeypatch.setattr(papers_mod.random, "shuffle", lambda _xs: None)
    monkeypatch.setattr(papers_mod.random, "random", lambda: 0.0)

    recent_time = datetime.now(timezone.utc)
    # 4 concepts → target max(2, floor(4*0.5)=2)=2; two fresh ask_count=0 available
    candidates = _fake_questions(
        [
            ("recent1", "A", 1, recent_time),
            ("recent2", "A", 1, recent_time),
            ("fresh1", "B", 0, None),
            ("fresh2", "B", 0, None),
        ]
    )
    selected = papers_mod._select_questions_for_paper(
        db=None,
        candidates=candidates,
        user_id="u1",
    )
    assert {q.id for q in selected} == {"fresh1", "fresh2"}


def test_soft_cooldown_falls_back_when_fresh_pool_too_small(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from datetime import datetime, timezone
    from app.services import papers as papers_mod

    monkeypatch.setattr(papers_mod.settings, "PAPER_MIN_QUESTIONS", 3)
    monkeypatch.setattr(papers_mod.settings, "PAPER_SIZE_RATIO", 1.0)
    monkeypatch.setattr(papers_mod.settings, "PAPER_MAX_QUESTIONS", 100)
    monkeypatch.setattr(papers_mod, "_recent_paper_ids", lambda db, user_id: {"p1"})
    monkeypatch.setattr(
        papers_mod,
        "_question_ids_on_papers",
        lambda db, paper_ids: {"cooled1", "cooled2"},
    )
    monkeypatch.setattr(papers_mod.random, "shuffle", lambda _xs: None)
    monkeypatch.setattr(papers_mod.random, "random", lambda: 0.0)

    recent_time = datetime.now(timezone.utc)
    # Need all 3; only 1 fresh → must reuse cooled (least-asked among them)
    candidates = _fake_questions(
        [
            ("fresh1", "A", 0, None),
            ("cooled1", "A", 1, recent_time),
            ("cooled2", "B", 5, recent_time),
        ]
    )
    selected = papers_mod._select_questions_for_paper(
        db=None,
        candidates=candidates,
        user_id="u1",
    )
    assert len(selected) == 3
    assert {q.id for q in selected} == {"fresh1", "cooled1", "cooled2"}


def test_multi_topic_round_robin_gives_each_topic_a_slot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services import papers as papers_mod

    monkeypatch.setattr(papers_mod.settings, "PAPER_MIN_QUESTIONS", 3)
    monkeypatch.setattr(papers_mod.settings, "PAPER_SIZE_RATIO", 0.5)
    monkeypatch.setattr(papers_mod.settings, "PAPER_MAX_QUESTIONS", 100)
    monkeypatch.setattr(papers_mod, "_recent_paper_ids", lambda db, user_id: set())
    monkeypatch.setattr(
        papers_mod, "_question_ids_on_papers", lambda db, paper_ids: set()
    )
    monkeypatch.setattr(papers_mod.random, "shuffle", lambda xs: None)
    monkeypatch.setattr(papers_mod.random, "random", lambda: 0.0)

    # 6 concepts → target max(3, floor(6*0.5)=3)=3
    # Topic A has many never-asked; without RR, A could take all 3 slots.
    candidates = _fake_questions(
        [
            ("a1", "Polity", 0, None),
            ("a2", "Polity", 0, None),
            ("a3", "Polity", 0, None),
            ("a4", "Polity", 0, None),
            ("b1", "Economy", 0, None),
            ("c1", "History", 0, None),
        ]
    )
    selected = papers_mod._select_questions_for_paper(
        db=None,
        candidates=candidates,
        user_id="u1",
    )
    topics = {q.topic for q in selected}
    assert len(selected) == 3
    assert topics == {"Polity", "Economy", "History"}


def test_generate_paper_requires_ready_note(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _auth(monkeypatch)
    monkeypatch.setattr(
        "app.services.notes.upload_pdf",
        lambda **kwargs: kwargs["key"],
    )

    upload = client.post(
        "/notes",
        headers={"Authorization": "Bearer t"},
        files={"file": ("n.pdf", b"%PDF-1.4", "application/pdf")},
        data={"title": "Not ready"},
    )
    note_id = upload.json()["id"]

    resp = client.post(
        f"/notes/{note_id}/generate-paper",
        headers={"Authorization": "Bearer t"},
        json={"language": "en"},
    )
    assert resp.status_code == 400
    detail = resp.json()["detail"]
    assert "prepared" in detail.lower() or "Ready" in detail


def test_generate_paper_success(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _auth(monkeypatch)
    monkeypatch.setattr(
        "app.services.notes.upload_pdf",
        lambda **kwargs: kwargs["key"],
    )
    monkeypatch.setattr(
        "app.services.note_processing.download_pdf",
        lambda **kwargs: b"%PDF-fake%",
    )
    monkeypatch.setattr(
        "app.services.note_processing.extract_text_from_pdf",
        lambda _pdf: (
            "Article 14 Equality before law. Article 15 Prohibition of discrimination. "
            "Article 19 Freedom of speech. Article 21 Right to life and personal liberty. "
            "These fundamental rights form the core of the Indian Constitution for exams."
        ),
    )
    monkeypatch.setattr(
        "app.services.papers.generate_mcqs_from_notes",
        lambda _canonical, output_language="en", **_kwargs: [
            {
                "variant_group_id": "g1",
                "topic": "Equality",
                "stem": "Article 14 guarantees?",
                "options": ["Equality", "Speech", "Religion", "Property"],
                "correct_index": 0,
                "explanation": "Equality before law",
            },
            {
                "variant_group_id": "g1",
                "topic": "Equality",
                "stem": "Which article is equality before law?",
                "options": ["14", "15", "19", "21"],
                "correct_index": 0,
                "explanation": "Article 14",
            },
            {
                "variant_group_id": "g2",
                "topic": "Speech",
                "stem": "Article 19 protects?",
                "options": ["Speech", "Equality", "Life", "Property"],
                "correct_index": 0,
                "explanation": "Freedom of speech",
            },
            {
                "variant_group_id": "g3",
                "topic": "Life",
                "stem": "Article 21 is about?",
                "options": ["Life", "Speech", "Equality", "Religion"],
                "correct_index": 0,
                "explanation": "Right to life",
            },
            {
                "variant_group_id": "g4",
                "topic": "Discrimination",
                "stem": "Article 15 prohibits?",
                "options": ["Discrimination", "Speech", "Trade", "Assembly"],
                "correct_index": 0,
                "explanation": "Non-discrimination",
            },
            {
                "variant_group_id": "g5",
                "topic": "General",
                "stem": "Fundamental rights are in?",
                "options": ["Part III", "Part IV", "Part I", "Part II"],
                "correct_index": 0,
                "explanation": "Part III",
            },
        ],
    )

    upload = client.post(
        "/notes",
        headers={"Authorization": "Bearer t"},
        files={"file": ("rights.pdf", b"%PDF-1.4", "application/pdf")},
        data={"title": "Rights", "language": "en"},
    )
    note_id = upload.json()["id"]

    client.post(
        f"/notes/{note_id}/process",
        headers={"Authorization": "Bearer t"},
    )

    paper = client.post(
        f"/notes/{note_id}/generate-paper",
        headers={"Authorization": "Bearer t"},
        json={"language": "en"},
    )
    assert paper.status_code == 200, paper.text
    body = paper.json()
    assert body["language"] == "en"
    assert body["question_count"] >= 1
    assert len(body["questions"]) == body["question_count"]
    # At most one question per variant group
    groups = [q["variant_group_id"] for q in body["questions"]]
    assert len(groups) == len(set(groups))

    detail = client.get(
        f"/papers/{body['id']}",
        headers={"Authorization": "Bearer t"},
    )
    assert detail.status_code == 200
    assert detail.json()["id"] == body["id"]

    me = client.get("/me", headers={"Authorization": "Bearer t"})
    assert me.json()["preferred_paper_language"] == "en"
