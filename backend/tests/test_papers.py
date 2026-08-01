"""Paper generation tests with mocked OpenAI / R2."""

import pytest
from fastapi.testclient import TestClient


def _auth(monkeypatch: pytest.MonkeyPatch, uid: str = "user-paper-1") -> None:
    monkeypatch.setattr(
        "app.core.deps.verify_firebase_token",
        lambda _token: {"uid": uid, "phone_number": "+919700011122"},
    )


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
    assert "Ready" in resp.json()["detail"]


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
        "app.services.papers.download_pdf",
        lambda **kwargs: b"%PDF-fake%",
    )
    monkeypatch.setattr(
        "app.services.papers.pdf_page_count",
        lambda _pdf: 2,
    )
    monkeypatch.setattr(
        "app.services.papers.generate_mcqs_from_notes",
        lambda _canonical, output_language="en": [
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
