"""Pytest bootstrap — set test env before app imports."""

import os

os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["FIREBASE_PROJECT_ID"] = "test-project"
os.environ["FIREBASE_CREDENTIALS_PATH"] = "missing-credentials.json"

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
