"""Question paper endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas import PaperDetailResponse, PaperQuestionResponse, PaperSummaryResponse
from app.services import papers as papers_service

router = APIRouter(prefix="/papers", tags=["papers"])


def _summary(paper) -> PaperSummaryResponse:
    return PaperSummaryResponse(
        id=paper.id,
        note_id=paper.note_id,
        title=paper.title,
        language=paper.language,
        status=paper.status,
        question_count=paper.question_count,
        created_at=paper.created_at,
    )


def _detail(db: Session, paper) -> PaperDetailResponse:
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
            correct_index=question.correct_index,
            explanation=question.explanation,
            topic=question.topic,
            variant_group_id=question.variant_group_id,
        )
        for link, question in rows
    ]
    base = _summary(paper)
    return PaperDetailResponse(**base.model_dump(), questions=questions)


@router.get("", response_model=list[PaperSummaryResponse])
def list_papers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PaperSummaryResponse]:
    papers = papers_service.list_papers_for_user(db, user_id=current_user.id)
    return [_summary(p) for p in papers]


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
