"""Question paper and attempt endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas import (
    AttemptAnswerReview,
    AttemptResponse,
    AttemptSubmitRequest,
    PaperDetailResponse,
    PaperQuestionResponse,
    PaperRenameRequest,
    PaperSummaryResponse,
    TestTopicFolderResponse,
)
from app.services import attempts as attempts_service
from app.services import entity_ops
from app.services import papers as papers_service

router = APIRouter(prefix="/papers", tags=["papers"])


def _summary(paper) -> PaperSummaryResponse:
    return PaperSummaryResponse(
        id=paper.id,
        note_id=paper.note_id,
        batch_folder_id=paper.batch_folder_id,
        title=paper.title,
        language=paper.language,
        status=paper.status,
        question_count=paper.question_count,
        created_at=paper.created_at,
    )


def _summary_from_dict(data: dict) -> PaperSummaryResponse:
    return PaperSummaryResponse(
        id=data["id"],
        note_id=data.get("note_id"),
        batch_folder_id=data.get("batch_folder_id"),
        title=data["title"],
        language=data["language"],
        status=data["status"],
        question_count=data["question_count"],
        created_at=data["created_at"],
    )


def _question_for_attempt(link, question) -> PaperQuestionResponse:
    """Omit correct answers so the client can run a fair attempt."""
    return PaperQuestionResponse(
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


def _detail(db: Session, paper) -> PaperDetailResponse:
    rows = papers_service.list_paper_questions(db, paper_id=paper.id)
    questions = [_question_for_attempt(link, question) for link, question in rows]
    base = _summary(paper)
    return PaperDetailResponse(**base.model_dump(), questions=questions)


def _attempt_response(db: Session, attempt) -> AttemptResponse:
    total = attempt.total_count or 0
    correct = attempt.correct_count or 0
    percent = int(round((correct / total) * 100)) if total else 0
    review_rows = attempts_service.build_attempt_review(db, attempt=attempt)
    answers = [AttemptAnswerReview(**row) for row in review_rows]
    return AttemptResponse(
        id=attempt.id,
        paper_id=attempt.paper_id,
        correct_count=correct,
        total_count=total,
        score_percent=percent,
        submitted_at=attempt.submitted_at,
        answers=answers,
    )


@router.get("", response_model=list[PaperSummaryResponse])
def list_papers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PaperSummaryResponse]:
    papers = papers_service.list_papers_for_user(db, user_id=current_user.id)
    return [_summary(p) for p in papers]


@router.get("/topics", response_model=list[TestTopicFolderResponse])
def list_test_topic_folders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TestTopicFolderResponse]:
    folders = papers_service.list_test_topic_folders(db, user_id=current_user.id)
    return [
        TestTopicFolderResponse(
            topic_id=f["topic_id"],
            topic_name=f["topic_name"],
            latest_test_at=f["latest_test_at"],
            test_count=f["test_count"],
            tests=[_summary_from_dict(t) for t in f["tests"]],
        )
        for f in folders
    ]


@router.get("/{paper_id}", response_model=PaperDetailResponse)
def get_paper(
    paper_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaperDetailResponse:
    paper = papers_service.get_paper_for_user(
        db,
        paper_id=paper_id,
        user_id=current_user.id,
    )
    return _detail(db, paper)


@router.patch("/{paper_id}", response_model=PaperSummaryResponse)
def rename_paper(
    paper_id: str,
    body: PaperRenameRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaperSummaryResponse:
    paper = entity_ops.rename_paper(
        db, paper_id=paper_id, user_id=current_user.id, title=body.title
    )
    return _summary(paper)


@router.post("/{paper_id}/attempts", response_model=AttemptResponse)
def submit_paper_attempt(
    paper_id: str,
    body: AttemptSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AttemptResponse:
    attempt = attempts_service.submit_attempt(
        db,
        user_id=current_user.id,
        paper_id=paper_id,
        answers=[a.model_dump() for a in body.answers],
    )
    return _attempt_response(db, attempt)


@router.get("/{paper_id}/attempts/{attempt_id}", response_model=AttemptResponse)
def get_paper_attempt(
    paper_id: str,
    attempt_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AttemptResponse:
    papers_service.get_paper_for_user(
        db,
        paper_id=paper_id,
        user_id=current_user.id,
    )
    attempt = attempts_service.get_attempt_for_user(
        db,
        attempt_id=attempt_id,
        user_id=current_user.id,
    )
    if attempt.paper_id != paper_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attempt not found",
        )
    return _attempt_response(db, attempt)
