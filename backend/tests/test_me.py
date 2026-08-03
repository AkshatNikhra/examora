"""Auth /me endpoint tests."""

import pytest
from fastapi.testclient import TestClient


def test_me_unauthorized_without_token(client: TestClient) -> None:
    response = client.get("/me")
    assert response.status_code == 401


def test_me_upserts_user_from_firebase_claims(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.core.deps.verify_firebase_token",
        lambda _token: {"uid": "firebase-uid-1", "phone_number": "+919999999999"},
    )

    response = client.get(
        "/me",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "firebase-uid-1"
    assert body["phone"] == "+919999999999"
    assert body["account_type"] == "USER"
    assert "created_at" in body
