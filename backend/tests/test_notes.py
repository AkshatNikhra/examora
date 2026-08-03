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
    body = detail.json()
    assert body["id"] == note_id
    # Detail is metadata-only — OCR / AI text is not exposed on GET /notes/{id}.
    assert "raw_extracted_text" not in body
    assert "canonical_content_en" not in body
    assert body["can_delete"] is True

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
        lambda _pdf: (
            "Article 14 Equality before law. Article 15 Prohibition of discrimination. "
            "Article 19 Freedom of speech. Article 21 Right to life and personal liberty. "
            "These fundamental rights form the core of the Indian Constitution for exams."
        ),
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
    detail_body = detail.json()
    assert detail_body["status"] == "ready"
    assert detail_body["has_canonical"] is True
    assert detail_body["can_delete"] is False
    assert "raw_extracted_text" not in detail_body
    assert "canonical_content_en" not in detail_body


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
    monkeypatch.setattr(
        "app.services.note_processing.extract_text_from_pdf",
        lambda _pdf: "",
    )

    def _ocr_fail(_pdf: bytes, **_kwargs: object) -> str:
        raise ValueError("OCR found no readable text")

    monkeypatch.setattr(
        "app.ai.ocr_vision.ocr_pdf_with_vision",
        _ocr_fail,
    )
    # Re-enable OCR path for this test
    monkeypatch.setattr(
        "app.services.note_processing.settings.OCR_PROVIDER",
        "google_vision",
    )
    monkeypatch.setattr(
        "app.services.note_processing.settings.OCR_MIN_TEXT_CHARS",
        100,
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
    assert "ocr" in (status.json()["error_message"] or "").lower()


def test_process_note_uses_ocr_when_extract_empty(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "app.core.deps.verify_firebase_token",
        lambda _token: {"uid": "user-notes-4", "phone_number": "+919888877773"},
    )
    monkeypatch.setattr(
        "app.services.notes.upload_pdf",
        lambda **kwargs: kwargs["key"],
    )
    monkeypatch.setattr(
        "app.services.note_processing.download_pdf",
        lambda **kwargs: b"%PDF-scan%",
    )
    monkeypatch.setattr(
        "app.services.note_processing.extract_text_from_pdf",
        lambda _pdf: "",
    )
    monkeypatch.setattr(
        "app.ai.ocr_vision.ocr_pdf_with_vision",
        lambda _pdf, **_kwargs: "अनुच्छेद 14 समानता का अधिकार\nArticle 14 Equality.",
    )
    monkeypatch.setattr(
        "app.services.note_processing.settings.OCR_PROVIDER",
        "google_vision",
    )

    upload = client.post(
        "/notes",
        headers={"Authorization": "Bearer test-token"},
        files={"file": ("handwritten.pdf", b"%PDF-1.4", "application/pdf")},
        data={"title": "Handwritten", "language": "hi"},
    )
    note_id = upload.json()["id"]

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
    status_body = status.json()
    assert status_body["status"] == "ready"
    assert status_body["has_canonical"] is True
    assert "Article 14" in (status_body["canonical_preview"] or "")
    assert status_body.get("raw_preview")

    detail = client.get(
        f"/notes/{note_id}",
        headers={"Authorization": "Bearer test-token"},
    )
    assert detail.status_code == 200
    body = detail.json()
    assert body["status"] == "ready"
    assert body["has_canonical"] is True
    assert body["can_delete"] is False
    assert "raw_extracted_text" not in body
    assert "canonical_content_en" not in body
