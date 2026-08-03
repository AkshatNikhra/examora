"""Account-type limit resolution + code-flow usage (OCR / paper create)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.limits import limits_for
from app.models import AccountType, User


def test_limits_for_uses_tier_env_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.core.limits.settings.OCR_MAX_PAGES", 20)
    monkeypatch.setattr("app.core.limits.settings.OCR_MAX_PAGES_ADMIN", 1000)
    monkeypatch.setattr("app.core.limits.settings.OCR_MAX_PAGES_DEV", 100)
    monkeypatch.setattr("app.core.limits.settings.OCR_MAX_PAGES_TESTER", 50)
    monkeypatch.setattr("app.core.limits.settings.NOTE_AI_MAX_CHUNKS", 1)
    monkeypatch.setattr("app.core.limits.settings.NOTE_AI_MAX_CHUNKS_ADMIN", 200)
    monkeypatch.setattr("app.core.limits.settings.NOTE_AI_MAX_CHUNKS_DEV", 50)
    monkeypatch.setattr("app.core.limits.settings.NOTE_AI_MAX_CHUNKS_TESTER", 20)
    monkeypatch.setattr("app.core.limits.settings.PAPER_MAX_PAGES", 20)
    monkeypatch.setattr("app.core.limits.settings.PAPER_MAX_PAGES_ADMIN", 1000)
    monkeypatch.setattr("app.core.limits.settings.PAPER_MAX_PAGES_DEV", 100)
    monkeypatch.setattr("app.core.limits.settings.PAPER_MAX_PAGES_TESTER", 50)
    monkeypatch.setattr("app.core.limits.settings.PAPER_MONTHLY_CREATE_LIMIT", 4)
    monkeypatch.setattr(
        "app.core.limits.settings.PAPER_MONTHLY_CREATE_LIMIT_ADMIN", 100
    )
    monkeypatch.setattr(
        "app.core.limits.settings.PAPER_MONTHLY_CREATE_LIMIT_DEV", 100
    )
    monkeypatch.setattr(
        "app.core.limits.settings.PAPER_MONTHLY_CREATE_LIMIT_TESTER", 20
    )

    assert limits_for("USER").ocr_max_pages == 20
    assert limits_for(AccountType.ADMIN).ocr_max_pages == 1000
    assert limits_for("DEV").note_ai_max_chunks == 50
    assert limits_for("TESTER").paper_max_pages == 50
    assert limits_for("ADMIN").paper_monthly_create_limit == 100
    assert limits_for("weird").ocr_max_pages == 20  # unknown → USER


def test_limits_for_includes_paper_mcq_max_chunks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.core.limits.settings.PAPER_MCQ_MAX_CHUNKS", 20)
    monkeypatch.setattr("app.core.limits.settings.PAPER_MCQ_MAX_CHUNKS_ADMIN", 200)
    monkeypatch.setattr("app.core.limits.settings.PAPER_MCQ_MAX_CHUNKS_DEV", 50)
    monkeypatch.setattr("app.core.limits.settings.PAPER_MCQ_MAX_CHUNKS_TESTER", 20)
    assert limits_for("USER").paper_mcq_max_chunks == 20
    assert limits_for("ADMIN").paper_mcq_max_chunks == 200
    assert limits_for("DEV").paper_mcq_max_chunks == 50


def _auth(monkeypatch: pytest.MonkeyPatch, uid: str, phone: str) -> None:
    monkeypatch.setattr(
        "app.core.deps.verify_firebase_token",
        lambda _token: {"uid": uid, "phone_number": phone},
    )


def _set_account_type(uid: str, account_type: str) -> None:
    db = SessionLocal()
    try:
        user = db.get(User, uid)
        assert user is not None
        user.account_type = account_type
        db.commit()
    finally:
        db.close()


def _mcq_payload():
    return [
        {
            "variant_group_id": f"g{i}",
            "topic": f"T{i}",
            "stem": f"Question {i}?",
            "options": ["A", "B", "C", "D"],
            "correct_index": 0,
            "explanation": "Because notes say so",
        }
        for i in range(1, 7)
    ]


def test_process_note_passes_ocr_max_pages_for_account_type(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    uid = "user-limits-ocr"
    _auth(monkeypatch, uid, "+919700000001")
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
        lambda _pdf: "",
    )
    monkeypatch.setattr(
        "app.services.note_processing.settings.OCR_PROVIDER",
        "google_vision",
    )
    monkeypatch.setattr("app.core.limits.settings.OCR_MAX_PAGES", 20)
    monkeypatch.setattr("app.core.limits.settings.OCR_MAX_PAGES_ADMIN", 1000)

    captured: dict[str, int | None] = {"max_pages": None}

    def _fake_ocr(_pdf: bytes, *, max_pages: int | None = None) -> str:
        captured["max_pages"] = max_pages
        return (
            "Article 14 Equality before law. Article 15 Prohibition of discrimination. "
            "Article 19 Freedom of speech. Article 21 Right to life and personal liberty."
        )

    monkeypatch.setattr("app.ai.ocr_vision.ocr_pdf_with_vision", _fake_ocr)

    upload = client.post(
        "/notes",
        headers={"Authorization": "Bearer t"},
        files={"file": ("scan.pdf", b"%PDF-1.4", "application/pdf")},
        data={"title": "Scan", "language": "en"},
    )
    assert upload.status_code == 201
    note_id = upload.json()["id"]

    # Default USER → OCR_MAX_PAGES
    processed = client.post(
        f"/notes/{note_id}/process",
        headers={"Authorization": "Bearer t"},
    )
    assert processed.status_code == 200
    assert captured["max_pages"] == 20

    # Promote to ADMIN and re-process → OCR_MAX_PAGES_ADMIN
    _set_account_type(uid, AccountType.ADMIN.value)
    captured["max_pages"] = None
    processed_admin = client.post(
        f"/notes/{note_id}/process",
        headers={"Authorization": "Bearer t"},
    )
    assert processed_admin.status_code == 200
    assert captured["max_pages"] == 1000


def test_upload_allows_large_page_count(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    uid = "user-limits-upload-pages"
    _auth(monkeypatch, uid, "+919700000004")
    monkeypatch.setattr(
        "app.services.notes.upload_pdf",
        lambda **kwargs: kwargs["key"],
    )
    monkeypatch.setattr("app.services.notes.pdf_page_count", lambda _pdf: 250)

    allowed = client.post(
        "/notes",
        headers={"Authorization": "Bearer t"},
        files={"file": ("long.pdf", b"%PDF-1.4", "application/pdf")},
        data={"title": "Long notes", "language": "en"},
    )
    assert allowed.status_code == 201


def test_generate_paper_does_not_enforce_page_limit(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    uid = "user-limits-paper"
    _auth(monkeypatch, uid, "+919700000002")
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
        lambda _canonical, output_language="en", **_kwargs: _mcq_payload(),
    )
    monkeypatch.setattr("app.core.limits.settings.PAPER_MONTHLY_CREATE_LIMIT", 100)

    upload = client.post(
        "/notes",
        headers={"Authorization": "Bearer t"},
        files={"file": ("long.pdf", b"%PDF-1.4", "application/pdf")},
        data={"title": "Long notes", "language": "en"},
    )
    assert upload.status_code == 201
    note_id = upload.json()["id"]

    process = client.post(
        f"/notes/{note_id}/process",
        headers={"Authorization": "Bearer t"},
    )
    assert process.status_code == 200

    paper = client.post(
        f"/notes/{note_id}/generate-paper",
        headers={"Authorization": "Bearer t"},
        json={"language": "en"},
    )
    assert paper.status_code == 200
    assert paper.json()["status"] == "ready"


def test_me_defaults_account_type_user(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _auth(monkeypatch, "user-limits-me", "+919700000003")
    response = client.get("/me", headers={"Authorization": "Bearer t"})
    assert response.status_code == 200
    assert response.json()["account_type"] == "USER"
