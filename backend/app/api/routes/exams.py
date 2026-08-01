"""Exam and batch-folder endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas import (
    BatchFolderCreate,
    BatchFolderResponse,
    ExamCreate,
    ExamResponse,
    ExamUploadHintResponse,
    GenerateFromTopicsRequest,
    GeneratePaperRequest,
    NoteResponse,
    PaperDetailResponse,
    PaperQuestionResponse,
)
from app.services import exams as exams_service
from app.services import papers as papers_service

router = APIRouter(tags=["exams"])


def _exam_response(db: Session, exam) -> ExamResponse:
    return ExamResponse(
        id=exam.id,
        name=exam.name,
        created_at=exam.created_at,
        batch_count=exams_service.batch_count(db, exam_id=exam.id),
        badge=getattr(exam, "badge", None),
    )


def _batch_response(db: Session, batch) -> BatchFolderResponse:
    return BatchFolderResponse(
        id=batch.id,
        exam_id=batch.exam_id,
        name=batch.name,
        created_at=batch.created_at,
        note_count=exams_service.note_count_for_batch(db, batch_id=batch.id),
        has_paper=exams_service.batch_has_paper(db, batch_id=batch.id),
    )


def _paper_detail(db: Session, paper) -> PaperDetailResponse:
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


@router.get("/exams", response_model=list[ExamResponse])
def list_exams(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ExamResponse]:
    exams = exams_service.list_exams(db, user_id=current_user.id)
    return [_exam_response(db, e) for e in exams]


@router.post("/exams", response_model=ExamResponse, status_code=201)
def create_exam(
    body: ExamCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExamResponse:
    exam = exams_service.create_exam(db, user_id=current_user.id, name=body.name)
    return _exam_response(db, exam)


@router.get("/exams/{exam_id}", response_model=ExamResponse)
def get_exam(
    exam_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExamResponse:
    exam = exams_service.get_exam_for_user(
        db, exam_id=exam_id, user_id=current_user.id
    )
    return _exam_response(db, exam)


@router.get("/exams/{exam_id}/upload-hint", response_model=ExamUploadHintResponse)
def exam_upload_hint(
    exam_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExamUploadHintResponse:
    hint = exams_service.upload_hint_for_exam(
        db, exam_id=exam_id, user_id=current_user.id
    )
    return ExamUploadHintResponse(**hint)


@router.get("/exams/{exam_id}/batches", response_model=list[BatchFolderResponse])
def list_batches(
    exam_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[BatchFolderResponse]:
    batches = exams_service.list_batches(
        db, user_id=current_user.id, exam_id=exam_id
    )
    return [_batch_response(db, b) for b in batches]


@router.post(
    "/exams/{exam_id}/batches",
    response_model=BatchFolderResponse,
    status_code=201,
)
def create_batch(
    exam_id: str,
    body: BatchFolderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BatchFolderResponse:
    batch = exams_service.create_batch(
        db,
        user_id=current_user.id,
        exam_id=exam_id,
        name=body.name,
    )
    return _batch_response(db, batch)


@router.get("/batches/{batch_id}", response_model=BatchFolderResponse)
def get_batch(
    batch_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BatchFolderResponse:
    batch = exams_service.get_batch_for_user(
        db, batch_id=batch_id, user_id=current_user.id
    )
    return _batch_response(db, batch)


@router.get("/batches/{batch_id}/notes", response_model=list[NoteResponse])
def list_batch_notes(
    batch_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[NoteResponse]:
    notes = exams_service.list_notes_in_batch(
        db, batch_id=batch_id, user_id=current_user.id
    )
    return [NoteResponse.from_note(n) for n in notes]


@router.post("/batches/{batch_id}/generate-paper", response_model=PaperDetailResponse)
def generate_paper_from_batch(
    batch_id: str,
    body: GeneratePaperRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaperDetailResponse:
    language = body.language if body else None
    paper = papers_service.generate_paper_for_batch(
        db,
        user=current_user,
        batch_id=batch_id,
        language=language,
    )
    return _paper_detail(db, paper)


@router.post("/exams/{exam_id}/generate-paper", response_model=PaperDetailResponse)
def generate_paper_from_topics(
    exam_id: str,
    body: GenerateFromTopicsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaperDetailResponse:
    exams_service.get_exam_for_user(db, exam_id=exam_id, user_id=current_user.id)
    # Ensure every batch belongs to this exam
    for bid in body.batch_ids:
        batch = exams_service.get_batch_for_user(
            db, batch_id=bid, user_id=current_user.id
        )
        if batch.exam_id != exam_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="All topics must belong to this exam",
            )
    paper = papers_service.generate_paper_for_batches(
        db,
        user=current_user,
        batch_ids=body.batch_ids,
        language=body.language,
    )
    return _paper_detail(db, paper)
