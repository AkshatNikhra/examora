"""Notes upload, listing, and processing endpoints."""

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import Note, NoteStatus, User
from app.schemas import (
    GeneratePaperRequest,
    NoteFileUrlResponse,
    NoteRenameRequest,
    NoteResponse,
    NoteStatusResponse,
    PaperDetailResponse,
    PaperQuestionResponse,
)
from app.services import entity_ops
from app.services import note_processing, notes as notes_service
from app.services import papers as papers_service
from app.services.r2 import download_pdf, presign_pdf_get_url

router = APIRouter(prefix="/notes", tags=["notes"])


def _to_response(note: Note) -> NoteResponse:
    return NoteResponse.from_note(note)


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


def _safe_pdf_filename(title: str) -> str:
    base = "".join(c for c in (title or "note").strip() if c.isalnum() or c in " ._-" )
    base = base.strip() or "note"
    if not base.lower().endswith(".pdf"):
        base = f"{base}.pdf"
    return base[:180]


@router.post("", response_model=NoteResponse, status_code=201)
async def upload_note(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    language: str = Form(default="en"),
    batch_folder_id: str | None = Form(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NoteResponse:
    note = await notes_service.create_note_from_upload(
        db,
        user=current_user,
        file=file,
        title=title,
        language=language,
        batch_folder_id=batch_folder_id,
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


@router.post("/{note_id}/generate-paper", response_model=PaperDetailResponse)
def generate_paper(
    note_id: str,
    body: GeneratePaperRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaperDetailResponse:
    language = body.language if body else None
    paper = papers_service.generate_paper_for_note(
        db,
        user=current_user,
        note_id=note_id,
        language=language,
    )
    rows = papers_service.list_paper_questions(db, paper_id=paper.id)
    questions = [
        PaperQuestionResponse(
            id=question.id,
            order_index=link.order_index,
            stem=question.stem,
            options=[
                question.option_a,
                question.option_b,
                question.option_c,
                question.option_d,
            ],
            topic=question.topic,
            variant_group_id=question.variant_group_id,
        )
        for link, question in rows
    ]
    return PaperDetailResponse(
        id=paper.id,
        note_id=paper.note_id,
        batch_folder_id=paper.batch_folder_id,
        title=paper.title,
        language=paper.language,
        status=paper.status,
        question_count=paper.question_count,
        created_at=paper.created_at,
        questions=questions,
    )


@router.get("/{note_id}/file")
def download_note_file(
    note_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """Authenticated PDF bytes — mobile saves locally and opens in the system PDF app."""
    note = notes_service.get_note_for_user(
        db,
        note_id=note_id,
        user_id=current_user.id,
    )
    data = download_pdf(key=note.file_url)
    filename = _safe_pdf_filename(note.title)
    return Response(
        content=data,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/{note_id}/file-url", response_model=NoteFileUrlResponse)
def note_file_url(
    note_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NoteFileUrlResponse:
    """Short-lived R2 URL (optional); prefer /file for reliable phone open)."""
    note = notes_service.get_note_for_user(
        db,
        note_id=note_id,
        user_id=current_user.id,
    )
    expires_in = 300
    url = presign_pdf_get_url(key=note.file_url, expires_in=expires_in)
    return NoteFileUrlResponse(
        url=url,
        expires_in=expires_in,
        filename=_safe_pdf_filename(note.title),
    )


@router.get("/{note_id}", response_model=NoteResponse)
def get_note(
    note_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NoteResponse:
    """Metadata only — OCR / AI text is not exposed to students."""
    note = notes_service.get_note_for_user(
        db,
        note_id=note_id,
        user_id=current_user.id,
    )
    return _to_response(note)


@router.patch("/{note_id}", response_model=NoteResponse)
def rename_note(
    note_id: str,
    body: NoteRenameRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NoteResponse:
    note = entity_ops.rename_note(
        db, note_id=note_id, user_id=current_user.id, title=body.title
    )
    return _to_response(note)


@router.delete("/{note_id}", status_code=204)
def delete_note(
    note_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    entity_ops.delete_note(db, note_id=note_id, user_id=current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
