"""Pytest bootstrap — set test env before app imports."""

import os

os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["FIREBASE_PROJECT_ID"] = "test-project"
os.environ["FIREBASE_CREDENTIALS_PATH"] = "missing-credentials.json"
os.environ["NOTE_AUTO_PROCESS"] = "false"
os.environ["NOTE_AI_PROVIDER"] = "local"
os.environ["OCR_PROVIDER"] = "none"

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(autouse=True)
def _default_upload_page_count(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fake PDF bytes in tests are not valid; default to 1 page on upload."""
    monkeypatch.setattr("app.services.notes.pdf_page_count", lambda _pdf: 1)


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
