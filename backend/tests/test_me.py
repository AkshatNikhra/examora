"""Auth /me endpoint tests."""

from datetime import datetime, timezone

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


def test_me_summary_includes_paper_quota(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.core.deps.verify_firebase_token",
        lambda _token: {
            "uid": "firebase-uid-summary",
            "phone_number": "+919888888888",
        },
    )
    monkeypatch.setattr(
        "app.core.limits.settings.PAPER_MONTHLY_CREATE_LIMIT",
        4,
    )

    assert client.get("/me", headers={"Authorization": "Bearer t"}).status_code == 200

    response = client.get("/me/summary", headers={"Authorization": "Bearer t"})
    assert response.status_code == 200
    body = response.json()
    quota = body["paper_quota"]
    assert quota["used"] == 0
    assert quota["limit"] == 4
    assert quota["remaining"] == 4
    resets = datetime.fromisoformat(quota["resets_at"].replace("Z", "+00:00"))
    assert resets.tzinfo is not None
    assert resets > datetime.now(timezone.utc)
