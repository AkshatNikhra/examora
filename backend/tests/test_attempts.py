"""Paper attempt / score tests with mocked MCQ generation."""

import pytest
from fastapi.testclient import TestClient


def _auth(monkeypatch: pytest.MonkeyPatch, uid: str = "user-attempt-1") -> None:
    monkeypatch.setattr(
        "app.core.deps.verify_firebase_token",
        lambda _token: {"uid": uid, "phone_number": "+919700033344"},
    )


def _mock_pipeline(monkeypatch: pytest.MonkeyPatch) -> None:
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


def _create_paper(client: TestClient) -> dict:
    upload = client.post(
        "/notes",
        headers={"Authorization": "Bearer t"},
        files={"file": ("rights.pdf", b"%PDF-1.4", "application/pdf")},
        data={"title": "Rights", "language": "en"},
    )
    note_id = upload.json()["id"]
    client.post(f"/notes/{note_id}/process", headers={"Authorization": "Bearer t"})
    paper = client.post(
        f"/notes/{note_id}/generate-paper",
        headers={"Authorization": "Bearer t"},
        json={"language": "en"},
    )
    assert paper.status_code == 200, paper.text
    return paper.json()


def test_paper_hides_answers_until_submit(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _auth(monkeypatch)
    _mock_pipeline(monkeypatch)
    body = _create_paper(client)

    for q in body["questions"]:
        assert q.get("correct_index") is None
        assert q.get("explanation") is None

    detail = client.get(
        f"/papers/{body['id']}",
        headers={"Authorization": "Bearer t"},
    )
    assert detail.status_code == 200
    for q in detail.json()["questions"]:
        assert q.get("correct_index") is None


def test_submit_attempt_scores(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _auth(monkeypatch)
    _mock_pipeline(monkeypatch)
    body = _create_paper(client)
    questions = body["questions"]
    assert len(questions) >= 1

    # All correct (index 0 in fixtures)
    payload = {
        "answers": [
            {"question_id": q["id"], "selected_index": 0} for q in questions
        ]
    }
    resp = client.post(
        f"/papers/{body['id']}/attempts",
        headers={"Authorization": "Bearer t"},
        json=payload,
    )
    assert resp.status_code == 200, resp.text
    result = resp.json()
    assert result["correct_count"] == result["total_count"]
    assert result["score_percent"] == 100
    assert len(result["answers"]) == len(questions)
    assert all(a["is_correct"] for a in result["answers"])
    assert all(a["correct_index"] == 0 for a in result["answers"])

    fetched = client.get(
        f"/papers/{body['id']}/attempts/{result['id']}",
        headers={"Authorization": "Bearer t"},
    )
    assert fetched.status_code == 200
    assert fetched.json()["id"] == result["id"]


def test_submit_attempt_partial_score(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _auth(monkeypatch)
    _mock_pipeline(monkeypatch)
    body = _create_paper(client)
    questions = body["questions"]

    answers = []
    for i, q in enumerate(questions):
        # first correct, rest wrong
        answers.append(
            {"question_id": q["id"], "selected_index": 0 if i == 0 else 1}
        )

    resp = client.post(
        f"/papers/{body['id']}/attempts",
        headers={"Authorization": "Bearer t"},
        json={"answers": answers},
    )
    assert resp.status_code == 200, resp.text
    result = resp.json()
    assert result["correct_count"] == 1
    assert result["total_count"] == len(questions)
    assert result["score_percent"] == int(round(100 / len(questions)))
