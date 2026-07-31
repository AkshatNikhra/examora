"""Notes API tests with mocked R2 upload."""

from io import BytesIO

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
