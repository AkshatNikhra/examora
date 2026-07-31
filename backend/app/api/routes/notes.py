"""Notes upload and listing endpoints."""

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import Note, User
from app.schemas import NoteResponse
from app.services import notes as notes_service

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("", response_model=NoteResponse, status_code=201)
async def upload_note(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    language: str = Form(default="en"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Note:
    return await notes_service.create_note_from_upload(
        db,
        user=current_user,
        file=file,
        title=title,
        language=language,
    )


@router.get("", response_model=list[NoteResponse])
def list_notes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Note]:
    return notes_service.list_notes_for_user(db, user_id=current_user.id)


@router.get("/{note_id}", response_model=NoteResponse)
def get_note(
    note_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Note:
    return notes_service.get_note_for_user(
        db,
        note_id=note_id,
        user_id=current_user.id,
    )
