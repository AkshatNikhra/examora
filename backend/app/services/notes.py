"""Note create / query helpers."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.pdf_extract import pdf_page_count
from app.core.config import settings
from app.core.limits import limits_for
from app.models import BatchFolder, Note, NoteStatus, User
from app.services.r2 import download_pdf, upload_pdf

logger = logging.getLogger(__name__)


def _page_count_or_reject(raw: bytes) -> int:
    try:
        return pdf_page_count(raw)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid PDF: {exc}",
        ) from exc


def _existing_batch_page_total(db: Session, *, batch_folder_id: str) -> int:
    notes = list(
        db.scalars(select(Note).where(Note.batch_folder_id == batch_folder_id)).all()
    )
    total = 0
    for note in notes:
        try:
            total += pdf_page_count(download_pdf(key=note.file_url))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not count pages for note %s: %s", note.id, exc)
    return total


async def create_note_from_upload(
    db: Session,
    *,
    user: User,
    file: UploadFile,
    title: str | None,
    language: str,
    batch_folder_id: str | None = None,
) -> Note:
    if file.content_type not in {"application/pdf", "application/x-pdf", "application/octet-stream"}:
        # Some clients send octet-stream; still require .pdf extension.
        filename = (file.filename or "").lower()
        if not filename.endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported",
            )

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")
    if len(raw) > settings.MAX_PDF_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"PDF exceeds max size of {settings.MAX_PDF_SIZE_BYTES} bytes",
        )

    pages = _page_count_or_reject(raw)
    max_pages = limits_for(user.account_type).paper_max_pages
    if pages > max_pages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"PDF has {pages} pages; max allowed is {max_pages}. "
                "Split or shorten the PDF before uploading."
            ),
        )

    resolved_batch_id: str | None = None
    if batch_folder_id:
        batch = db.get(BatchFolder, batch_folder_id)
        if batch is None or batch.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Batch folder not found",
            )
        existing = _existing_batch_page_total(db, batch_folder_id=batch.id)
        if existing + pages > max_pages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"This PDF has {pages} pages; the batch already has about {existing}. "
                    f"Max allowed per batch is {max_pages}. "
                    "Upload into a new batch or use a shorter PDF."
                ),
            )
        resolved_batch_id = batch.id

    note_id = str(uuid.uuid4())
    original_name = Path(file.filename or "notes.pdf").name
    safe_title = (title or original_name).strip() or "Untitled notes"
    object_key = f"notes/{user.id}/{note_id}.pdf"

    upload_pdf(key=object_key, body=raw, content_type="application/pdf")

    note = Note(
        id=note_id,
        user_id=user.id,
        batch_folder_id=resolved_batch_id,
        title=safe_title[:255],
        file_url=object_key,
        language=(language or "en").strip().lower()[:16] or "en",
        status=NoteStatus.UPLOADED.value,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def list_notes_for_user(db: Session, *, user_id: str) -> list[Note]:
    stmt = (
        select(Note)
        .where(Note.user_id == user_id)
        .order_by(Note.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def get_note_for_user(db: Session, *, note_id: str, user_id: str) -> Note:
    note = db.get(Note, note_id)
    if note is None or note.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return note
