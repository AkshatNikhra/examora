"""Rename + delete helpers with product rules for exams / topics / notes / papers."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models import (
    AttemptAnswer,
    BatchFolder,
    Exam,
    Note,
    NoteStatus,
    PaperAttempt,
    PaperBatchLink,
    PaperQuestion,
    Question,
    QuestionPaper,
)
from app.services import exams as exams_service
from app.services.note_processing import refresh_topic_canonical
from app.services.notes import get_note_for_user
from app.services.papers import get_paper_for_user
from app.services.r2 import delete_pdf


def _clean_name(value: str, *, field: str) -> str:
    cleaned = (value or "").strip()
    if not cleaned:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field} is required",
        )
    return cleaned[:255]


def batch_has_ready_note(db: Session, *, batch_id: str) -> bool:
    stmt = (
        select(Note.id)
        .where(
            Note.batch_folder_id == batch_id,
            Note.status == NoteStatus.READY.value,
        )
        .limit(1)
    )
    return db.scalars(stmt).first() is not None


def exam_has_ready_note(db: Session, *, exam_id: str) -> bool:
    stmt = (
        select(Note.id)
        .join(BatchFolder, Note.batch_folder_id == BatchFolder.id)
        .where(
            BatchFolder.exam_id == exam_id,
            Note.status == NoteStatus.READY.value,
        )
        .limit(1)
    )
    return db.scalars(stmt).first() is not None


def exam_can_delete(db: Session, *, exam_id: str) -> bool:
    """Empty exam, or topics exist but none contain a Ready note."""
    return not exam_has_ready_note(db, exam_id=exam_id)


def batch_can_delete(db: Session, *, batch_id: str) -> bool:
    return not batch_has_ready_note(db, batch_id=batch_id)


def note_can_delete(note: Note) -> bool:
    return note.status != NoteStatus.READY.value


# ── Rename ──────────────────────────────────────────────────────────────────


def rename_exam(db: Session, *, exam_id: str, user_id: str, name: str) -> Exam:
    exam = exams_service.get_exam_for_user(db, exam_id=exam_id, user_id=user_id)
    exam.name = _clean_name(name, field="Exam name")
    from app.services.catalog import _badge_from_name

    exam.badge = _badge_from_name(exam.name)
    db.commit()
    db.refresh(exam)
    return exam


def rename_batch(db: Session, *, batch_id: str, user_id: str, name: str) -> BatchFolder:
    batch = exams_service.get_batch_for_user(db, batch_id=batch_id, user_id=user_id)
    batch.name = _clean_name(name, field="Topic name")
    db.commit()
    db.refresh(batch)
    return batch


def rename_note(db: Session, *, note_id: str, user_id: str, title: str) -> Note:
    note = get_note_for_user(db, note_id=note_id, user_id=user_id)
    note.title = _clean_name(title, field="Note title")
    db.commit()
    db.refresh(note)
    return note


def rename_paper(
    db: Session, *, paper_id: str, user_id: str, title: str
) -> QuestionPaper:
    paper = get_paper_for_user(db, paper_id=paper_id, user_id=user_id)
    paper.title = _clean_name(title, field="Test title")
    db.commit()
    db.refresh(paper)
    return paper


# ── Delete helpers ───────────────────────────────────────────────────────────


def _paper_ids_for_batch(db: Session, *, batch_id: str) -> list[str]:
    linked = list(
        db.scalars(
            select(PaperBatchLink.paper_id).where(PaperBatchLink.batch_id == batch_id)
        ).all()
    )
    direct = list(
        db.scalars(
            select(QuestionPaper.id).where(QuestionPaper.batch_folder_id == batch_id)
        ).all()
    )
    return list({str(pid) for pid in (*linked, *direct)})


def _delete_papers(db: Session, *, paper_ids: list[str]) -> None:
    if not paper_ids:
        return

    attempt_ids = list(
        db.scalars(
            select(PaperAttempt.id).where(PaperAttempt.paper_id.in_(paper_ids))
        ).all()
    )
    if attempt_ids:
        db.execute(
            delete(AttemptAnswer).where(AttemptAnswer.attempt_id.in_(attempt_ids))
        )
        db.execute(delete(PaperAttempt).where(PaperAttempt.id.in_(attempt_ids)))

    db.execute(delete(PaperQuestion).where(PaperQuestion.paper_id.in_(paper_ids)))
    db.execute(delete(PaperBatchLink).where(PaperBatchLink.paper_id.in_(paper_ids)))
    db.execute(delete(QuestionPaper).where(QuestionPaper.id.in_(paper_ids)))


def _unlink_batch_from_papers(db: Session, *, batch_id: str) -> None:
    """
    Detach a topic from its papers.

    Multi-topic papers that still link other topics are kept (link row removed only).
    Papers that only belonged to this topic are hard-deleted.
    """
    paper_ids = _paper_ids_for_batch(db, batch_id=batch_id)
    if not paper_ids:
        return

    db.execute(
        delete(PaperBatchLink).where(
            PaperBatchLink.batch_id == batch_id,
            PaperBatchLink.paper_id.in_(paper_ids),
        )
    )

    orphaned: list[str] = []
    for pid in paper_ids:
        paper = db.get(QuestionPaper, pid)
        if paper is None:
            continue

        remaining = [
            str(bid)
            for bid in db.scalars(
                select(PaperBatchLink.batch_id).where(PaperBatchLink.paper_id == pid)
            ).all()
        ]

        if paper.batch_folder_id == batch_id:
            paper.batch_folder_id = remaining[0] if remaining else None
            db.add(paper)

        still_linked = bool(remaining) or (paper.batch_folder_id is not None)
        if not still_linked:
            orphaned.append(pid)

    _delete_papers(db, paper_ids=orphaned)


def _delete_note_row(db: Session, *, note: Note, purge_r2: bool = True) -> None:
    """Hard-delete a note and dependent questions/paper links. Caller enforces Ready rule."""
    note_id = note.id
    object_key = note.file_url

    question_ids = list(
        db.scalars(select(Question.id).where(Question.note_id == note_id)).all()
    )
    paper_ids: list[str] = []
    if question_ids:
        paper_ids.extend(
            str(pid)
            for pid in db.scalars(
                select(PaperQuestion.paper_id).where(
                    PaperQuestion.question_id.in_(question_ids)
                )
            ).all()
        )
        db.execute(
            delete(PaperQuestion).where(PaperQuestion.question_id.in_(question_ids))
        )

    paper_ids.extend(
        str(pid)
        for pid in db.scalars(
            select(QuestionPaper.id).where(QuestionPaper.note_id == note_id)
        ).all()
    )
    _delete_papers(db, paper_ids=list(set(paper_ids)))

    if question_ids:
        db.execute(delete(Question).where(Question.id.in_(question_ids)))

    db.delete(note)
    db.flush()

    if purge_r2:
        delete_pdf(key=object_key)


def delete_note(db: Session, *, note_id: str, user_id: str) -> None:
    note = get_note_for_user(db, note_id=note_id, user_id=user_id)
    if not note_can_delete(note):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ready notes cannot be deleted. They power your topic content and tests.",
        )
    batch_id = note.batch_folder_id
    _delete_note_row(db, note=note)
    if batch_id:
        refresh_topic_canonical(db, batch_folder_id=batch_id)
    db.commit()


def delete_batch(db: Session, *, batch_id: str, user_id: str) -> None:
    batch = exams_service.get_batch_for_user(db, batch_id=batch_id, user_id=user_id)
    if not batch_can_delete(db, batch_id=batch.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This topic has a Ready note and cannot be deleted. "
                "Ready notes cannot be removed."
            ),
        )

    # Unlink this topic from papers; keep multi-topic papers that still have other topics.
    _unlink_batch_from_papers(db, batch_id=batch.id)

    notes = list(
        db.scalars(select(Note).where(Note.batch_folder_id == batch.id)).all()
    )
    for note in notes:
        _delete_note_row(db, note=note)

    db.delete(batch)
    db.commit()


def delete_exam(db: Session, *, exam_id: str, user_id: str) -> None:
    exam = exams_service.get_exam_for_user(db, exam_id=exam_id, user_id=user_id)
    if not exam_can_delete(db, exam_id=exam.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This exam has a topic with a Ready note and cannot be deleted. "
                "Ready notes cannot be removed."
            ),
        )

    batches = list(
        db.scalars(select(BatchFolder).where(BatchFolder.exam_id == exam.id)).all()
    )
    for batch in batches:
        if not batch_can_delete(db, batch_id=batch.id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This exam has a topic with a Ready note and cannot be deleted.",
            )
        # Whole exam is going away — hard-delete papers owned by these topics.
        paper_ids = _paper_ids_for_batch(db, batch_id=batch.id)
        _delete_papers(db, paper_ids=paper_ids)
        notes = list(
            db.scalars(select(Note).where(Note.batch_folder_id == batch.id)).all()
        )
        for note in notes:
            _delete_note_row(db, note=note)
        db.delete(batch)

    db.delete(exam)
    db.commit()


def ready_note_count_for_batch(db: Session, *, batch_id: str) -> int:
    stmt = (
        select(func.count())
        .select_from(Note)
        .where(
            Note.batch_folder_id == batch_id,
            Note.status == NoteStatus.READY.value,
        )
    )
    return int(db.scalar(stmt) or 0)


def ready_note_count_for_exam(db: Session, *, exam_id: str) -> int:
    stmt = (
        select(func.count())
        .select_from(Note)
        .join(BatchFolder, Note.batch_folder_id == BatchFolder.id)
        .where(
            BatchFolder.exam_id == exam_id,
            Note.status == NoteStatus.READY.value,
        )
    )
    return int(db.scalar(stmt) or 0)
