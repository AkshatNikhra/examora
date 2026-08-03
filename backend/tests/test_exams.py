"""Phase 4b exam + batch folder tests."""

import pytest
from fastapi.testclient import TestClient


def _auth(
    monkeypatch: pytest.MonkeyPatch,
    uid: str = "user-exam-1",
    phone: str = "+919700055566",
) -> None:
    monkeypatch.setattr(
        "app.core.deps.verify_firebase_token",
        lambda _token: {"uid": uid, "phone_number": phone},
    )


def _mock_mcq(monkeypatch: pytest.MonkeyPatch) -> None:
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
            "Article 19 Freedom of speech. Article 21 Right to life and personal liberty."
        ),
    )
    monkeypatch.setattr(
        "app.services.papers.generate_mcqs_from_notes",
        lambda _canonical, output_language="en", **_kwargs: [
            {
                "variant_group_id": f"g{i}",
                "topic": "Rights",
                "stem": f"Question {i}?",
                "options": ["A", "B", "C", "D"],
                "correct_index": 0,
                "explanation": "Because",
            }
            for i in range(1, 6)
        ],
    )


def test_exam_batch_upload_and_generate(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _auth(monkeypatch)
    _mock_mcq(monkeypatch)

    exam = client.post(
        "/exams",
        headers={"Authorization": "Bearer t"},
        json={"name": "UPSC Prelims"},
    )
    assert exam.status_code == 201, exam.text
    exam_id = exam.json()["id"]

    batch = client.post(
        f"/exams/{exam_id}/batches",
        headers={"Authorization": "Bearer t"},
        json={"name": "a"},
    )
    assert batch.status_code == 201, batch.text
    batch_id = batch.json()["id"]

    upload = client.post(
        "/notes",
        headers={"Authorization": "Bearer t"},
        files={"file": ("n.pdf", b"%PDF-1.4", "application/pdf")},
        data={"title": "Polity", "batch_folder_id": batch_id},
    )
    assert upload.status_code == 201, upload.text
    assert upload.json()["batch_folder_id"] == batch_id
    note_id = upload.json()["id"]

    client.post(f"/notes/{note_id}/process", headers={"Authorization": "Bearer t"})

    hint_before = client.get(
        f"/exams/{exam_id}/upload-hint",
        headers={"Authorization": "Bearer t"},
    )
    assert hint_before.json()["suggest_new_batch"] is False

    paper = client.post(
        f"/batches/{batch_id}/generate-paper",
        headers={"Authorization": "Bearer t"},
        json={"language": "en"},
    )
    assert paper.status_code == 200, paper.text
    assert paper.json()["batch_folder_id"] == batch_id

    hint_after = client.get(
        f"/exams/{exam_id}/upload-hint",
        headers={"Authorization": "Bearer t"},
    )
    assert hint_after.json()["suggest_new_batch"] is True
    assert batch_id in hint_after.json()["batches_with_papers"]

    notes = client.get(
        f"/batches/{batch_id}/notes",
        headers={"Authorization": "Bearer t"},
    )
    assert len(notes.json()) == 1

    detail = client.get(
        f"/batches/{batch_id}",
        headers={"Authorization": "Bearer t"},
    )
    assert detail.status_code == 200
    assert detail.json()["has_canonical"] is True
    assert "Article 14" in (detail.json()["canonical_preview"] or "")


def test_topic_canonical_and_per_topic_mcq_calls(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _auth(monkeypatch, uid="user-exam-topics", phone="+919700055577")
    _mock_mcq(monkeypatch)

    calls: list[str] = []

    def _capture(canonical: str, output_language: str = "en", **_kwargs):
        calls.append(canonical[:40])
        return [
            {
                "variant_group_id": f"g{len(calls)}-{i}",
                "topic": "Rights",
                "stem": f"Q{len(calls)}-{i}?",
                "options": ["A", "B", "C", "D"],
                "correct_index": 0,
                "explanation": "Because",
            }
            for i in range(1, 6)
        ]

    monkeypatch.setattr(
        "app.services.papers.generate_mcqs_from_notes",
        _capture,
    )

    exam = client.post(
        "/exams",
        headers={"Authorization": "Bearer t"},
        json={"name": "State PSC"},
    )
    exam_id = exam.json()["id"]

    batch_a = client.post(
        f"/exams/{exam_id}/batches",
        headers={"Authorization": "Bearer t"},
        json={"name": "Topic A"},
    ).json()["id"]
    batch_b = client.post(
        f"/exams/{exam_id}/batches",
        headers={"Authorization": "Bearer t"},
        json={"name": "Topic B"},
    ).json()["id"]

    for batch_id, title in ((batch_a, "A.pdf"), (batch_b, "B.pdf")):
        up = client.post(
            "/notes",
            headers={"Authorization": "Bearer t"},
            files={"file": (title, b"%PDF-1.4", "application/pdf")},
            data={"title": title, "batch_folder_id": batch_id},
        )
        assert up.status_code == 201
        client.post(
            f"/notes/{up.json()['id']}/process",
            headers={"Authorization": "Bearer t"},
        )

    from app.core.database import SessionLocal
    from app.models import BatchFolder

    db = SessionLocal()
    try:
        a = db.get(BatchFolder, batch_a)
        b = db.get(BatchFolder, batch_b)
        assert a is not None and (a.canonical_content_en or "").strip()
        assert b is not None and (b.canonical_content_en or "").strip()
        assert "Article 14" in (a.canonical_content_en or "")
    finally:
        db.close()

    paper = client.post(
        f"/exams/{exam_id}/generate-paper",
        headers={"Authorization": "Bearer t"},
        json={"batch_ids": [batch_a, batch_b], "language": "en"},
    )
    assert paper.status_code == 200, paper.text
    assert len(calls) == 2
