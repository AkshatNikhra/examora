"""Create practice papers from Ready notes (pool + assemble)."""

from __future__ import annotations

import hashlib
import logging
import math
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.generate_mcqs import generate_mcqs_from_notes
from app.ai.pdf_extract import pdf_page_count
from app.core.config import settings
from app.models import (
    BatchFolder,
    Note,
    NoteStatus,
    PaperQuestion,
    PaperStatus,
    Question,
    QuestionPaper,
    User,
)
from app.services.r2 import download_pdf

logger = logging.getLogger(__name__)


def _content_hash(stem: str, options: list[str]) -> str:
    raw = stem.lower().strip() + "|" + "|".join(o.lower().strip() for o in options)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _month_paper_count(db: Session, *, user_id: str) -> int:
    now = datetime.now(timezone.utc)
    start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    stmt = (
        select(func.count())
        .select_from(QuestionPaper)
        .where(
            QuestionPaper.user_id == user_id,
            QuestionPaper.created_at >= start,
            QuestionPaper.status == PaperStatus.READY.value,
        )
    )
    return int(db.scalar(stmt) or 0)


def _enforce_quota(db: Session, *, user_id: str) -> None:
    used = _month_paper_count(db, user_id=user_id)
    if used >= settings.PAPER_MONTHLY_CREATE_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Monthly paper create limit reached "
                f"({settings.PAPER_MONTHLY_CREATE_LIMIT}). Try again next month."
            ),
        )


def _page_count_for_note(note: Note) -> int:
    try:
        pdf_bytes = download_pdf(key=note.file_url)
        return pdf_page_count(pdf_bytes)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not count PDF pages for note %s: %s", note.id, exc)
        return 0


def _enforce_page_limit(note: Note) -> None:
    pages = _page_count_for_note(note)
    if pages > settings.PAPER_MAX_PAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Note has {pages} pages; max allowed per create is "
                f"{settings.PAPER_MAX_PAGES}. Use a shorter PDF for V1."
            ),
        )


def _enforce_batch_page_limit(notes: list[Note]) -> None:
    total = 0
    for note in notes:
        total += _page_count_for_note(note)
    if total > settings.PAPER_MAX_PAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Batch has about {total} pages across notes; max allowed per create is "
                f"{settings.PAPER_MAX_PAGES}. Split into a new batch folder."
            ),
        )


def _resolve_language(user: User, language: str | None) -> str:
    lang = (language or user.preferred_paper_language or "").strip().lower()
    if lang not in {"en", "hi"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="preferred_paper_language required: pass language=en or language=hi",
        )
    return lang



def _is_on_cooldown(question: Question, recent_paper_ids: set[str], db: Session) -> bool:
    now = datetime.now(timezone.utc)
    if question.last_asked_at is not None:
        asked = question.last_asked_at
        if asked.tzinfo is None:
            asked = asked.replace(tzinfo=timezone.utc)
        if now - asked < timedelta(days=settings.PAPER_COOLDOWN_DAYS):
            return True

    if not recent_paper_ids:
        return False

    stmt = select(PaperQuestion.paper_id).where(
        PaperQuestion.question_id == question.id,
        PaperQuestion.paper_id.in_(recent_paper_ids),
    )
    return db.scalars(stmt).first() is not None


def _recent_paper_ids(db: Session, *, user_id: str) -> set[str]:
    stmt = (
        select(QuestionPaper.id)
        .where(
            QuestionPaper.user_id == user_id,
            QuestionPaper.status == PaperStatus.READY.value,
        )
        .order_by(QuestionPaper.created_at.desc())
        .limit(settings.PAPER_COOLDOWN_GENERATIONS)
    )
    return set(db.scalars(stmt).all())


def _target_paper_size(unique_available: int) -> int:
    if unique_available <= 0:
        return 0
    sized = max(
        settings.PAPER_MIN_QUESTIONS,
        int(math.floor(unique_available * settings.PAPER_SIZE_RATIO)),
    )
    return max(1, min(sized, settings.PAPER_MAX_QUESTIONS, unique_available))


def _select_questions_for_paper(
    db: Session,
    *,
    candidates: list[Question],
    user_id: str,
) -> list[Question]:
    recent_ids = _recent_paper_ids(db, user_id=user_id)
    by_group: dict[str, list[Question]] = defaultdict(list)
    for q in candidates:
        if _is_on_cooldown(q, recent_ids, db):
            continue
        by_group[q.variant_group_id].append(q)

    # One pick per variant group; prefer never-asked, then older last_asked
    picks: list[Question] = []
    for group_questions in by_group.values():
        group_questions.sort(
            key=lambda q: (
                q.ask_count,
                q.last_asked_at or datetime.min.replace(tzinfo=timezone.utc),
            )
        )
        picks.append(group_questions[0])

    # Topic spread: round-robin by topic
    by_topic: dict[str, list[Question]] = defaultdict(list)
    for q in picks:
        by_topic[q.topic or "General"].append(q)

    ordered: list[Question] = []
    topics = sorted(by_topic.keys())
    while any(by_topic[t] for t in topics):
        for topic in topics:
            if by_topic[topic]:
                ordered.append(by_topic[topic].pop(0))

    target = _target_paper_size(len(ordered))
    return ordered[:target]


def generate_paper_for_note(
    db: Session,
    *,
    user: User,
    note_id: str,
    language: str | None = None,
) -> QuestionPaper:
    note = db.get(Note, note_id)
    if note is None or note.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    if note.status != NoteStatus.READY.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Note must be Ready before creating a paper. Process notes first.",
        )
    canonical = (note.canonical_content_en or "").strip()
    if not canonical:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Note has no English canonical content",
        )

    _enforce_quota(db, user_id=user.id)
    _enforce_page_limit(note)

    lang = _resolve_language(user, language)
    if user.preferred_paper_language != lang:
        user.preferred_paper_language = lang
        db.add(user)

    try:
        generated = generate_mcqs_from_notes(canonical, output_language=lang)
    except Exception as exc:  # noqa: BLE001
        logger.exception("MCQ generation failed for note %s", note_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to generate MCQs: {exc}",
        ) from exc

    for item in generated:
        options = item["options"]
        question = Question(
            id=str(uuid.uuid4()),
            user_id=user.id,
            note_id=note.id,
            variant_group_id=str(item["variant_group_id"])[:36],
            topic=item.get("topic"),
            stem=item["stem"],
            option_a=options[0],
            option_b=options[1],
            option_c=options[2],
            option_d=options[3],
            correct_index=item["correct_index"],
            explanation=item.get("explanation"),
            language=lang,
            content_hash=_content_hash(item["stem"], options),
            ask_count=0,
        )
        db.add(question)

    db.flush()

    existing = list(
        db.scalars(
            select(Question).where(
                Question.user_id == user.id,
                Question.note_id == note.id,
                Question.language == lang,
            )
        ).all()
    )
    selected = _select_questions_for_paper(db, candidates=existing, user_id=user.id)
    if not selected:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "No eligible questions after cooldown/filters. "
                "Try again later or process richer notes."
            ),
        )

    paper = QuestionPaper(
        id=str(uuid.uuid4()),
        user_id=user.id,
        note_id=note.id,
        batch_folder_id=note.batch_folder_id,
        language=lang,
        status=PaperStatus.READY.value,
        title=f"Practice — {note.title}"[:255],
        question_count=len(selected),
    )
    db.add(paper)
    db.flush()

    now = datetime.now(timezone.utc)
    for index, question in enumerate(selected):
        db.add(
            PaperQuestion(
                id=str(uuid.uuid4()),
                paper_id=paper.id,
                question_id=question.id,
                order_index=index,
            )
        )
        question.last_asked_at = now
        question.ask_count = (question.ask_count or 0) + 1
        db.add(question)

    db.commit()
    db.refresh(paper)
    return paper


def generate_paper_for_batch(
    db: Session,
    *,
    user: User,
    batch_id: str,
    language: str | None = None,
) -> QuestionPaper:
    batch = db.get(BatchFolder, batch_id)
    if batch is None or batch.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch folder not found",
        )

    notes = list(
        db.scalars(
            select(Note)
            .where(Note.batch_folder_id == batch.id, Note.user_id == user.id)
            .order_by(Note.created_at.asc())
        ).all()
    )
    if not notes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch has no notes. Upload PDFs first.",
        )

    _enforce_quota(db, user_id=user.id)
    _enforce_batch_page_limit(notes)

    ready = [
        n
        for n in notes
        if n.status == NoteStatus.READY.value
        and (n.canonical_content_en or "").strip()
    ]
    if not ready:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Process at least one note in this batch until Ready, then create a test.",
        )

    lang = _resolve_language(user, language)
    if user.preferred_paper_language != lang:
        user.preferred_paper_language = lang
        db.add(user)

    canonical = "\n\n".join(
        (n.canonical_content_en or "").strip() for n in ready
    ).strip()
    primary = ready[0]
    note_ids = [n.id for n in ready]

    try:
        generated = generate_mcqs_from_notes(canonical, output_language=lang)
    except Exception as exc:  # noqa: BLE001
        logger.exception("MCQ generation failed for batch %s", batch_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to generate MCQs: {exc}",
        ) from exc

    for item in generated:
        options = item["options"]
        question = Question(
            id=str(uuid.uuid4()),
            user_id=user.id,
            note_id=primary.id,
            variant_group_id=str(item["variant_group_id"])[:36],
            topic=item.get("topic"),
            stem=item["stem"],
            option_a=options[0],
            option_b=options[1],
            option_c=options[2],
            option_d=options[3],
            correct_index=item["correct_index"],
            explanation=item.get("explanation"),
            language=lang,
            content_hash=_content_hash(item["stem"], options),
            ask_count=0,
        )
        db.add(question)

    db.flush()

    existing = list(
        db.scalars(
            select(Question).where(
                Question.user_id == user.id,
                Question.note_id.in_(note_ids),
                Question.language == lang,
            )
        ).all()
    )
    selected = _select_questions_for_paper(db, candidates=existing, user_id=user.id)
    if not selected:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "No eligible questions after cooldown/filters. "
                "Try again later or add richer notes."
            ),
        )

    paper = QuestionPaper(
        id=str(uuid.uuid4()),
        user_id=user.id,
        note_id=primary.id,
        batch_folder_id=batch.id,
        language=lang,
        status=PaperStatus.READY.value,
        title=f"Practice — {batch.name}"[:255],
        question_count=len(selected),
    )
    db.add(paper)
    db.flush()

    now = datetime.now(timezone.utc)
    for index, question in enumerate(selected):
        db.add(
            PaperQuestion(
                id=str(uuid.uuid4()),
                paper_id=paper.id,
                question_id=question.id,
                order_index=index,
            )
        )
        question.last_asked_at = now
        question.ask_count = (question.ask_count or 0) + 1
        db.add(question)

    db.commit()
    db.refresh(paper)
    return paper


def get_paper_for_user(db: Session, *, paper_id: str, user_id: str) -> QuestionPaper:
    paper = db.get(QuestionPaper, paper_id)
    if paper is None or paper.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found")
    return paper


def list_papers_for_user(db: Session, *, user_id: str) -> list[QuestionPaper]:
    stmt = (
        select(QuestionPaper)
        .where(QuestionPaper.user_id == user_id)
        .order_by(QuestionPaper.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def list_paper_questions(db: Session, *, paper_id: str) -> list[tuple[PaperQuestion, Question]]:
    stmt = (
        select(PaperQuestion, Question)
        .join(Question, Question.id == PaperQuestion.question_id)
        .where(PaperQuestion.paper_id == paper_id)
        .order_by(PaperQuestion.order_index.asc())
    )
    return list(db.execute(stmt).all())
