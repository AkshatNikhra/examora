"""Notes API tests with mocked R2 upload / processing."""

import pytest
from fastapi.testclient import TestClient


def test_upload_note_requires_auth(client: TestClient) -> None:
    response = client.post(
        "/notes",
        files={"file": ("notes.pdf", b"%PDF-1.4 test", "application/pdf")},
    )
    assert response.status_code == 401


def test_upload_and_list_notes(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.core.deps.verify_firebase_token",
        lambda _token: {"uid": "user-notes-1", "phone_number": "+919888877776"},
    )
    monkeypatch.setattr(
        "app.services.notes.upload_pdf",
        lambda **kwargs: kwargs["key"],
    )

    upload = client.post(
        "/notes",
        headers={"Authorization": "Bearer test-token"},
        files={"file": ("polity.pdf", b"%PDF-1.4 fake-content", "application/pdf")},
        data={"title": "Polity notes", "language": "en"},
    )
    assert upload.status_code == 201
    body = upload.json()
    assert body["title"] == "Polity notes"
    assert body["status"] == "uploaded"
    assert body["user_id"] == "user-notes-1"
    assert body["has_canonical"] is False
    note_id = body["id"]

    listed = client.get(
        "/notes",
        headers={"Authorization": "Bearer test-token"},
    )
    assert listed.status_code == 200
    assert any(item["id"] == note_id for item in listed.json())

    detail = client.get(
        f"/notes/{note_id}",
        headers={"Authorization": "Bearer test-token"},
    )
    assert detail.status_code == 200
    assert detail.json()["id"] == note_id
    assert "raw_extracted_text" in detail.json()
    assert "canonical_content_en" in detail.json()

    status = client.get(
        f"/notes/{note_id}/status",
        headers={"Authorization": "Bearer test-token"},
    )
    assert status.status_code == 200
    assert status.json()["status"] == "uploaded"


def test_process_note_local_pipeline(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "app.core.deps.verify_firebase_token",
        lambda _token: {"uid": "user-notes-2", "phone_number": "+919888877775"},
    )
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
        lambda _pdf: "Article 14 Equality before law.\n\nArticle 21 Right to life.",
    )

    upload = client.post(
        "/notes",
        headers={"Authorization": "Bearer test-token"},
        files={"file": ("rights.pdf", b"%PDF-1.4 fake", "application/pdf")},
        data={"title": "Rights", "language": "en"},
    )
    assert upload.status_code == 201
    note_id = upload.json()["id"]

    # Auto-process disabled in tests — trigger manually (TestClient runs BackgroundTasks)
    processed = client.post(
        f"/notes/{note_id}/process",
        headers={"Authorization": "Bearer test-token"},
    )
    assert processed.status_code == 200

    status = client.get(
        f"/notes/{note_id}/status",
        headers={"Authorization": "Bearer test-token"},
    )
    assert status.status_code == 200
    body = status.json()
    assert body["status"] == "ready"
    assert body["has_canonical"] is True
    assert "Article 14" in (body["canonical_preview"] or "")
    assert body.get("raw_preview")

    detail = client.get(
        f"/notes/{note_id}",
        headers={"Authorization": "Bearer test-token"},
    )
    assert detail.status_code == 200
    assert "Article 14" in (detail.json()["raw_extracted_text"] or "")
    assert "Article 14" in (detail.json()["canonical_content_en"] or "")


def test_process_note_marks_failed_on_empty_pdf(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "app.core.deps.verify_firebase_token",
        lambda _token: {"uid": "user-notes-3", "phone_number": "+919888877774"},
    )
    monkeypatch.setattr(
        "app.services.notes.upload_pdf",
        lambda **kwargs: kwargs["key"],
    )
    monkeypatch.setattr(
        "app.services.note_processing.download_pdf",
        lambda **kwargs: b"%PDF-empty%",
    )

    def _raise_empty(_pdf: bytes) -> str:
        raise ValueError("No extractable text found")

    monkeypatch.setattr(
        "app.services.note_processing.extract_text_from_pdf",
        _raise_empty,
    )

    upload = client.post(
        "/notes",
        headers={"Authorization": "Bearer test-token"},
        files={"file": ("scan.pdf", b"%PDF-1.4", "application/pdf")},
        data={"title": "Scan"},
    )
    note_id = upload.json()["id"]

    client.post(
        f"/notes/{note_id}/process",
        headers={"Authorization": "Bearer test-token"},
    )
    status = client.get(
        f"/notes/{note_id}/status",
        headers={"Authorization": "Bearer test-token"},
    )
    assert status.json()["status"] == "failed"
    assert "extractable" in (status.json()["error_message"] or "").lower()
