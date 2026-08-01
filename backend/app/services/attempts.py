"""Submit and score practice paper attempts."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AttemptAnswer, PaperAttempt, Question
from app.services import papers as papers_service


def submit_attempt(
    db: Session,
    *,
    user_id: str,
    paper_id: str,
    answers: list[dict],
) -> PaperAttempt:
    paper = papers_service.get_paper_for_user(db, paper_id=paper_id, user_id=user_id)
    rows = papers_service.list_paper_questions(db, paper_id=paper.id)
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Paper has no questions",
        )

    by_qid: dict[str, tuple] = {question.id: (link, question) for link, question in rows}
    if len(answers) != len(by_qid):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Expected {len(by_qid)} answers, got {len(answers)}",
        )

    seen: set[str] = set()
    graded: list[tuple[Question, int, bool]] = []
    for item in answers:
        qid = item["question_id"]
        selected = int(item["selected_index"])
        if qid in seen:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate question_id in answers",
            )
        seen.add(qid)
        if qid not in by_qid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Question {qid} is not on this paper",
            )
        if selected < 0 or selected > 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="selected_index must be 0-3",
            )
        _link, question = by_qid[qid]
        is_correct = selected == question.correct_index
        graded.append((question, selected, is_correct))

    if seen != set(by_qid.keys()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Answers must cover every question on the paper",
        )

    correct_count = sum(1 for _q, _s, ok in graded if ok)
    attempt = PaperAttempt(
        id=str(uuid.uuid4()),
        user_id=user_id,
        paper_id=paper.id,
        correct_count=correct_count,
        total_count=len(graded),
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(attempt)
    db.flush()

    for question, selected, is_correct in graded:
        db.add(
            AttemptAnswer(
                id=str(uuid.uuid4()),
                attempt_id=attempt.id,
                question_id=question.id,
                selected_index=selected,
                is_correct=1 if is_correct else 0,
            )
        )

    db.commit()
    db.refresh(attempt)
    return attempt


def get_attempt_for_user(
    db: Session,
    *,
    attempt_id: str,
    user_id: str,
) -> PaperAttempt:
    attempt = db.get(PaperAttempt, attempt_id)
    if attempt is None or attempt.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attempt not found",
        )
    return attempt


def list_attempt_answers(
    db: Session,
    *,
    attempt_id: str,
) -> list[tuple[AttemptAnswer, Question]]:
    stmt = (
        select(AttemptAnswer, Question)
        .join(Question, Question.id == AttemptAnswer.question_id)
        .where(AttemptAnswer.attempt_id == attempt_id)
    )
    return list(db.execute(stmt).all())


def build_attempt_review(
    db: Session,
    *,
    attempt: PaperAttempt,
) -> list[dict]:
    paper_rows = papers_service.list_paper_questions(db, paper_id=attempt.paper_id)
    order_by_qid = {q.id: link.order_index for link, q in paper_rows}
    answer_rows = list_attempt_answers(db, attempt_id=attempt.id)
    review: list[dict] = []
    for answer, question in answer_rows:
        review.append(
            {
                "question_id": question.id,
                "order_index": order_by_qid.get(question.id, 0),
                "stem": question.stem,
                "options": [
                    question.option_a,
                    question.option_b,
                    question.option_c,
                    question.option_d,
                ],
                "selected_index": answer.selected_index,
                "correct_index": question.correct_index,
                "is_correct": bool(answer.is_correct),
                "explanation": question.explanation,
                "topic": question.topic,
            }
        )
    review.sort(key=lambda row: row["order_index"])
    return review
