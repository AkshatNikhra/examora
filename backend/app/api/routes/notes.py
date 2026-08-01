"""Notes upload, listing, and processing endpoints."""

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import Note, NoteStatus, User
from app.schemas import NoteDetailResponse, NoteResponse, NoteStatusResponse
from app.services import note_processing, notes as notes_service

router = APIRouter(prefix="/notes", tags=["notes"])


def _to_response(note: Note) -> NoteResponse:
    return NoteResponse.from_note(note)


def _to_detail(note: Note) -> NoteDetailResponse:
    return NoteDetailResponse.from_note(note)


def _status_response(note: Note) -> NoteStatusResponse:
    canonical = (note.canonical_content_en or "").strip()
    raw = (note.raw_extracted_text or "").strip()
    return NoteStatusResponse(
        id=note.id,
        status=note.status,
        source_language=note.source_language,
        error_message=note.error_message,
        processed_at=note.processed_at,
        has_canonical=bool(canonical),
        canonical_preview=canonical[:240] if canonical else None,
        raw_preview=raw[:240] if raw else None,
    )


@router.post("", response_model=NoteResponse, status_code=201)
async def upload_note(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    language: str = Form(default="en"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NoteResponse:
    note = await notes_service.create_note_from_upload(
        db,
        user=current_user,
        file=file,
        title=title,
        language=language,
    )
    if settings.NOTE_AUTO_PROCESS:
        background_tasks.add_task(note_processing.process_note_job, note.id)
    return _to_response(note)


@router.get("", response_model=list[NoteResponse])
def list_notes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[NoteResponse]:
    notes = notes_service.list_notes_for_user(db, user_id=current_user.id)
    return [_to_response(n) for n in notes]


@router.get("/{note_id}/status", response_model=NoteStatusResponse)
def get_note_status(
    note_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NoteStatusResponse:
    note = notes_service.get_note_for_user(
        db,
        note_id=note_id,
        user_id=current_user.id,
    )
    return _status_response(note)


@router.post("/{note_id}/process", response_model=NoteResponse)
def process_note(
    note_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NoteResponse:
    note = note_processing.enqueue_or_process(
        note_id=note_id,
        user_id=current_user.id,
        db=db,
    )
    if note.status == NoteStatus.PROCESSING.value:
        return _to_response(note)
    background_tasks.add_task(note_processing.process_note_job, note.id)
    return _to_response(note)


@router.get("/{note_id}", response_model=NoteDetailResponse)
def get_note(
    note_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NoteDetailResponse:
    note = notes_service.get_note_for_user(
        db,
        note_id=note_id,
        user_id=current_user.id,
    )
    return _to_detail(note)
