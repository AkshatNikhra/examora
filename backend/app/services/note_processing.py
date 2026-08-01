"""Background pipeline: R2 PDF → extract → understand → ready/failed."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.ai.pdf_extract import extract_text_from_pdf
from app.ai.understand import understand_notes
from app.core.database import SessionLocal
from app.models import Note, NoteStatus
from app.services.r2 import download_pdf

logger = logging.getLogger(__name__)


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
        raw_text = extract_text_from_pdf(pdf_bytes)
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
    # Allow re-run from uploaded / failed / ready
    note.status = NoteStatus.UPLOADED.value
    note.error_message = None
    db.commit()
    db.refresh(note)
    return note
