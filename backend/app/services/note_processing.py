"""Background pipeline: R2 PDF → extract or OCR → understand → ready/failed."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.ai.pdf_extract import extract_text_from_pdf
from app.ai.understand import understand_notes
from app.core.config import settings
from app.core.database import SessionLocal
from app.models import Note, NoteStatus
from app.services.r2 import download_pdf

logger = logging.getLogger(__name__)


def _needs_ocr(text: str) -> bool:
    return len((text or "").strip()) < settings.OCR_MIN_TEXT_CHARS


def _resolve_raw_text(pdf_bytes: bytes) -> tuple[str, str]:
    """
    Return (raw_text, source_label).
    source_label is 'extract' or 'ocr' for logging/UX later.
    """
    extracted = extract_text_from_pdf(pdf_bytes)
    provider = (settings.OCR_PROVIDER or "none").strip().lower()

    if not _needs_ocr(extracted):
        return extracted, "extract"

    if provider in {"", "none", "off"}:
        raise ValueError(
            "No extractable text found and OCR is disabled. "
            "Upload a typed PDF or enable OCR_PROVIDER=google_vision."
        )

    if provider != "google_vision":
        raise ValueError(f"Unsupported OCR_PROVIDER: {provider}")

    logger.info(
        "Weak/empty text extract (%s chars) — running Google Vision OCR (max %s pages)",
        len(extracted.strip()),
        settings.OCR_MAX_PAGES,
    )
    from app.ai.ocr_vision import ocr_pdf_with_vision

    ocr_text = ocr_pdf_with_vision(pdf_bytes, max_pages=settings.OCR_MAX_PAGES)
    return ocr_text, "ocr"


def process_note_job(note_id: str) -> None:
    """Run outside the request DB session (BackgroundTasks-safe)."""
    db = SessionLocal()
    try:
        process_note(db, note_id=note_id)
    finally:
        db.close()


def process_note(db: Session, *, note_id: str) -> Note:
    note = db.get(Note, note_id)
    if note is None:
        logger.warning("process_note: note %s not found", note_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    note.status = NoteStatus.PROCESSING.value
    note.error_message = None
    db.commit()

    try:
        pdf_bytes = download_pdf(key=note.file_url)
        raw_text, source = _resolve_raw_text(pdf_bytes)
        logger.info("Note %s text source=%s chars=%s", note_id, source, len(raw_text))
        canonical, source_language = understand_notes(
            raw_text,
            declared_language=note.language,
        )
        note.raw_extracted_text = raw_text
        note.canonical_content_en = canonical
        note.source_language = source_language or note.language
        note.error_message = None
        note.processed_at = datetime.now(timezone.utc)
        note.status = NoteStatus.READY.value
        db.commit()
        db.refresh(note)
        return note
    except Exception as exc:  # noqa: BLE001
        logger.exception("Note processing failed for %s", note_id)
        note.status = NoteStatus.FAILED.value
        note.error_message = str(exc)[:2000]
        note.processed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(note)
        return note


def enqueue_or_process(*, note_id: str, user_id: str, db: Session) -> Note:
    """Mark note processable and return current row (job runs separately)."""
    note = db.get(Note, note_id)
    if note is None or note.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    if note.status == NoteStatus.PROCESSING.value:
        return note
    note.status = NoteStatus.UPLOADED.value
    note.error_message = None
    db.commit()
    db.refresh(note)
    return note
