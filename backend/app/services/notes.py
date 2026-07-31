"""Note create / query helpers."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Note, NoteStatus, User
from app.services.r2 import upload_pdf


async def create_note_from_upload(
    db: Session,
    *,
    user: User,
    file: UploadFile,
    title: str | None,
    language: str,
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

    note_id = str(uuid.uuid4())
    original_name = Path(file.filename or "notes.pdf").name
    safe_title = (title or original_name).strip() or "Untitled notes"
    object_key = f"notes/{user.id}/{note_id}.pdf"

    upload_pdf(key=object_key, body=raw, content_type="application/pdf")

    note = Note(
        id=note_id,
        user_id=user.id,
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
