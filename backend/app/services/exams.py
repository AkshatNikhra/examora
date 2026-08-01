"""Exam and upload-batch helpers."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import BatchFolder, Exam, Note, QuestionPaper, PaperStatus


def create_exam(db: Session, *, user_id: str, name: str) -> Exam:
    cleaned = name.strip()
    if not cleaned:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exam name is required",
        )
    exam = Exam(
        id=str(uuid.uuid4()),
        user_id=user_id,
        name=cleaned[:255],
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)
    return exam


def list_exams(db: Session, *, user_id: str) -> list[Exam]:
    stmt = (
        select(Exam)
        .where(Exam.user_id == user_id)
        .order_by(Exam.created_at.asc())
    )
    return list(db.scalars(stmt).all())


def get_exam_for_user(db: Session, *, exam_id: str, user_id: str) -> Exam:
    exam = db.get(Exam, exam_id)
    if exam is None or exam.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found")
    return exam


def batch_count(db: Session, *, exam_id: str) -> int:
    stmt = select(func.count()).select_from(BatchFolder).where(BatchFolder.exam_id == exam_id)
    return int(db.scalar(stmt) or 0)


def create_batch(
    db: Session,
    *,
    user_id: str,
    exam_id: str,
    name: str,
) -> BatchFolder:
    get_exam_for_user(db, exam_id=exam_id, user_id=user_id)
    cleaned = name.strip()
    if not cleaned:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch folder name is required",
        )
    batch = BatchFolder(
        id=str(uuid.uuid4()),
        exam_id=exam_id,
        user_id=user_id,
        name=cleaned[:255],
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


def list_batches(db: Session, *, user_id: str, exam_id: str) -> list[BatchFolder]:
    get_exam_for_user(db, exam_id=exam_id, user_id=user_id)
    stmt = (
        select(BatchFolder)
        .where(BatchFolder.exam_id == exam_id, BatchFolder.user_id == user_id)
        .order_by(BatchFolder.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def get_batch_for_user(db: Session, *, batch_id: str, user_id: str) -> BatchFolder:
    batch = db.get(BatchFolder, batch_id)
    if batch is None or batch.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch folder not found",
        )
    return batch


def note_count_for_batch(db: Session, *, batch_id: str) -> int:
    stmt = select(func.count()).select_from(Note).where(Note.batch_folder_id == batch_id)
    return int(db.scalar(stmt) or 0)


def batch_has_paper(db: Session, *, batch_id: str) -> bool:
    stmt = (
        select(QuestionPaper.id)
        .where(
            QuestionPaper.batch_folder_id == batch_id,
            QuestionPaper.status == PaperStatus.READY.value,
        )
        .limit(1)
    )
    return db.scalars(stmt).first() is not None


def list_notes_in_batch(db: Session, *, batch_id: str, user_id: str) -> list[Note]:
    get_batch_for_user(db, batch_id=batch_id, user_id=user_id)
    stmt = (
        select(Note)
        .where(Note.batch_folder_id == batch_id, Note.user_id == user_id)
        .order_by(Note.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def upload_hint_for_exam(db: Session, *, exam_id: str, user_id: str) -> dict:
    """After any batch in this exam has a paper, nudge user toward a new batch."""
    get_exam_for_user(db, exam_id=exam_id, user_id=user_id)
    batches = list_batches(db, user_id=user_id, exam_id=exam_id)
    with_papers = [b.id for b in batches if batch_has_paper(db, batch_id=b.id)]
    suggest = len(with_papers) > 0
    return {
        "suggest_new_batch": suggest,
        "reason": (
            "A practice test was already created from a batch in this exam. "
            "Prefer a new upload batch, or choose an existing one."
            if suggest
            else None
        ),
        "batches_with_papers": with_papers,
    }
