"""Create practice papers from Ready notes (pool + assemble)."""

from __future__ import annotations

import hashlib
import logging
import math
import random
import re
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.generate_mcqs import generate_mcqs_from_notes
from app.core.config import settings
from app.core.limits import limits_for
from app.models import (
    BatchFolder,
    Note,
    NoteStatus,
    PaperBatchLink,
    PaperQuestion,
    PaperStatus,
    Question,
    QuestionPaper,
    User,
)
from app.services.note_processing import process_note, refresh_topic_canonical

logger = logging.getLogger(__name__)


def _content_hash(stem: str, options: list[str]) -> str:
    raw = stem.lower().strip() + "|" + "|".join(o.lower().strip() for o in options)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _batch_ids_for_paper(db: Session, *, paper: QuestionPaper) -> frozenset[str]:
    linked = list(
        db.scalars(
            select(PaperBatchLink.batch_id).where(PaperBatchLink.paper_id == paper.id)
        ).all()
    )
    if linked:
        return frozenset(str(bid) for bid in linked)
    if paper.batch_folder_id:
        return frozenset({paper.batch_folder_id})
    return frozenset()


def _build_paper_title(
    db: Session,
    *,
    user_id: str,
    batches: list[BatchFolder],
) -> str:
    """
    Single topic → Test-1, Test-2, …
    Multi topic  → MultiTopic-Test-1, MultiTopic-Test-2, … (one shared title on the paper)
    """
    batch_ids = frozenset(b.id for b in batches)
    papers = list(
        db.scalars(select(QuestionPaper).where(QuestionPaper.user_id == user_id)).all()
    )
    if len(batches) <= 1:
        matching = sum(
            1 for p in papers if _batch_ids_for_paper(db, paper=p) == batch_ids
        )
        return f"Test-{matching + 1}"
    matching = sum(
        1 for p in papers if len(_batch_ids_for_paper(db, paper=p)) > 1
    )
    return f"MultiTopic-Test-{matching + 1}"


def _display_titles_for_papers(
    db: Session,
    *,
    papers: list[QuestionPaper],
) -> dict[str, str]:
    """Canonical Test-N / MultiTopic-Test-N names by creation order (oldest = 1)."""
    chronological = sorted(
        papers,
        key=lambda p: p.created_at or datetime.min.replace(tzinfo=timezone.utc),
    )
    titles: dict[str, str] = {}
    multi_n = 0
    single_n_by_batches: dict[frozenset[str], int] = defaultdict(int)
    for paper in chronological:
        batch_ids = _batch_ids_for_paper(db, paper=paper)
        if len(batch_ids) > 1:
            multi_n += 1
            titles[paper.id] = f"MultiTopic-Test-{multi_n}"
        else:
            single_n_by_batches[batch_ids] += 1
            titles[paper.id] = f"Test-{single_n_by_batches[batch_ids]}"
    return titles


def _is_auto_or_legacy_paper_title(title: str | None) -> bool:
    """True for system-generated / migratable titles — never overwrite user renames."""
    cleaned = (title or "").strip()
    if not cleaned:
        return True
    if cleaned.startswith("Practice —") or cleaned.startswith("Practice -"):
        return True
    if re.fullmatch(r"Test-\d+", cleaned):
        return True
    if re.fullmatch(r"MultiTopic-Test-\d+", cleaned):
        return True
    return False


def _canonicalize_user_paper_titles(db: Session, *, user_id: str) -> None:
    """
    Migrate legacy / auto titles to Test-N scheme.

    Custom titles (user rename) are left untouched.
    """
    papers = list(
        db.scalars(select(QuestionPaper).where(QuestionPaper.user_id == user_id)).all()
    )
    if not papers:
        return
    titles = _display_titles_for_papers(db, papers=papers)
    changed = False
    for paper in papers:
        if not _is_auto_or_legacy_paper_title(paper.title):
            continue
        new_title = titles.get(paper.id)
        if new_title and paper.title != new_title:
            paper.title = new_title
            db.add(paper)
            changed = True
    if changed:
        db.commit()
        for paper in papers:
            db.refresh(paper)


def list_test_topic_folders(db: Session, *, user_id: str) -> list[dict]:
    """
    Topic folders for Tests tab: only topics that have ≥1 paper.
    Folders ordered by most recent paper, then name.
    Papers inside each folder ordered newest first.
    Multi-topic papers appear under every linked topic.
    """
    _canonicalize_user_paper_titles(db, user_id=user_id)

    papers = list(
        db.scalars(
            select(QuestionPaper)
            .where(
                QuestionPaper.user_id == user_id,
                QuestionPaper.status == PaperStatus.READY.value,
            )
            .order_by(QuestionPaper.created_at.desc())
        ).all()
    )
    if not papers:
        return []

    # topic_id -> list of papers (may include multi papers)
    by_topic: dict[str, list[QuestionPaper]] = defaultdict(list)
    for paper in papers:
        batch_ids = _batch_ids_for_paper(db, paper=paper)
        for bid in batch_ids:
            by_topic[bid].append(paper)

    if not by_topic:
        return []

    folders: list[dict] = []
    for topic_id, topic_papers in by_topic.items():
        batch = db.get(BatchFolder, topic_id)
        if batch is None or batch.user_id != user_id:
            continue
        # Ensure newest first (already from global order, but re-sort)
        topic_papers_sorted = sorted(
            topic_papers,
            key=lambda p: p.created_at or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        latest = topic_papers_sorted[0].created_at
        folders.append(
            {
                "topic_id": topic_id,
                "topic_name": (batch.name or "").strip() or "Topic",
                "latest_test_at": latest,
                "test_count": len(topic_papers_sorted),
                "tests": [
                    {
                        "id": p.id,
                        "note_id": p.note_id,
                        "batch_folder_id": p.batch_folder_id,
                        "title": p.title,
                        "language": p.language,
                        "status": p.status,
                        "question_count": p.question_count,
                        "created_at": p.created_at,
                    }
                    for p in topic_papers_sorted
                ],
            }
        )

    folders.sort(
        key=lambda f: (
            -(f["latest_test_at"].timestamp() if f["latest_test_at"] else 0),
            (f["topic_name"] or "").lower(),
        )
    )
    return folders


def _quota_window_start(now: datetime | None = None) -> datetime:
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current - timedelta(days=int(settings.PAPER_CREATE_WINDOW_DAYS))


def _rolling_paper_count(db: Session, *, user_id: str, now: datetime | None = None) -> int:
    """Ready papers created within the rolling window (each occupies one create slot)."""
    start = _quota_window_start(now)
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


def _oldest_active_paper_created_at(
    db: Session, *, user_id: str, now: datetime | None = None
) -> datetime | None:
    """Oldest ready paper still inside the rolling window — drives next slot restore."""
    start = _quota_window_start(now)
    stmt = (
        select(QuestionPaper.created_at)
        .where(
            QuestionPaper.user_id == user_id,
            QuestionPaper.created_at >= start,
            QuestionPaper.status == PaperStatus.READY.value,
        )
        .order_by(QuestionPaper.created_at.asc())
        .limit(1)
    )
    return db.scalar(stmt)


def _next_slot_at(
    db: Session, *, user_id: str, now: datetime | None = None
) -> datetime:
    """
    When the next create slot frees.

    Each paper restores its slot PAPER_CREATE_WINDOW_DAYS after that paper was created
    (not after the last available attempt was used).
    """
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    oldest = _oldest_active_paper_created_at(db, user_id=user_id, now=current)
    if oldest is None:
        return current
    created = oldest
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return created + timedelta(days=int(settings.PAPER_CREATE_WINDOW_DAYS))


def paper_quota_for_user(db: Session, *, user: User) -> dict:
    """Rolling create-quota snapshot for home / create-test UI."""
    limits = limits_for(user.account_type)
    limit = int(limits.paper_monthly_create_limit)
    used = _rolling_paper_count(db, user_id=user.id)
    remaining = max(0, limit - used)
    return {
        "used": used,
        "limit": limit,
        "remaining": remaining,
        # Kept as resets_at for API compat — means "next create slot frees at".
        "resets_at": _next_slot_at(db, user_id=user.id),
        "window_days": int(settings.PAPER_CREATE_WINDOW_DAYS),
    }


def _enforce_quota(
    db: Session,
    *,
    user_id: str,
    monthly_limit: int,
) -> None:
    used = _rolling_paper_count(db, user_id=user_id)
    if used >= monthly_limit:
        next_at = _next_slot_at(db, user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Paper create limit reached ({monthly_limit} per "
                f"{int(settings.PAPER_CREATE_WINDOW_DAYS)} days). "
                f"A slot frees after {next_at.isoformat()}."
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



def _is_recently_used(
    question: Question,
    *,
    recent_question_ids: set[str],
    now: datetime,
) -> bool:
    """
    Soft cooldown signal (not a hard ban).

    True if the question appeared on one of the last PAPER_COOLDOWN_GENERATIONS
    papers, or was asked within PAPER_COOLDOWN_DAYS. Selection prefers questions
    where this is False, but will reuse cooled questions when the fresh pool is
    too small to fill the paper.
    """
    if question.id in recent_question_ids:
        return True
    if question.last_asked_at is None:
        return False
    asked = question.last_asked_at
    if asked.tzinfo is None:
        asked = asked.replace(tzinfo=timezone.utc)
    return now - asked < timedelta(days=settings.PAPER_COOLDOWN_DAYS)


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


def _question_ids_on_papers(db: Session, *, paper_ids: set[str]) -> set[str]:
    if not paper_ids:
        return set()
    stmt = select(PaperQuestion.question_id).where(
        PaperQuestion.paper_id.in_(paper_ids)
    )
    return set(db.scalars(stmt).all())


def _target_paper_size(unique_available: int) -> int:
    """
    Paper length = max(MIN, floor(available * RATIO)), then capped by MAX and pool size.

    Primary rule is the 30% ratio (plus a minimum of 5). PAPER_MAX_QUESTIONS is only a
    safety ceiling so huge pools cannot produce endless papers.
    """
    if unique_available <= 0:
        return 0
    sized = max(
        settings.PAPER_MIN_QUESTIONS,
        int(math.floor(unique_available * settings.PAPER_SIZE_RATIO)),
    )
    return max(1, min(sized, settings.PAPER_MAX_QUESTIONS, unique_available))


def _fairness_sort_key(question: Question, noise: float) -> tuple:
    asked = question.last_asked_at
    if asked is None:
        asked_key = datetime.min.replace(tzinfo=timezone.utc)
    else:
        asked_key = asked if asked.tzinfo else asked.replace(tzinfo=timezone.utc)
    return (int(question.ask_count or 0), asked_key, noise)


def _one_pick_per_variant_group(candidates: list[Question]) -> list[Question]:
    by_group: dict[str, list[Question]] = defaultdict(list)
    for q in candidates:
        by_group[q.variant_group_id].append(q)

    picks: list[Question] = []
    for group_questions in by_group.values():
        group_questions.sort(
            key=lambda q: (
                int(q.ask_count or 0),
                q.last_asked_at or datetime.min.replace(tzinfo=timezone.utc),
            )
        )
        picks.append(group_questions[0])
    return picks


def _topic_round_robin(questions: list[Question]) -> list[Question]:
    """
    Drain least-asked lists per topic in round-robin so multi-topic papers
    are not dominated by one large topic. Topic order itself is shuffled.
    """
    if not questions:
        return []

    by_topic: dict[str, list[Question]] = defaultdict(list)
    for q in questions:
        by_topic[(q.topic or "").strip() or "General"].append(q)

    for topic_questions in by_topic.values():
        noises = {id(q): random.random() for q in topic_questions}
        topic_questions.sort(key=lambda q: _fairness_sort_key(q, noises[id(q)]))

    topics = list(by_topic.keys())
    random.shuffle(topics)

    ordered: list[Question] = []
    while any(by_topic[t] for t in topics):
        for topic in topics:
            if by_topic[topic]:
                ordered.append(by_topic[topic].pop(0))
    return ordered


def _select_questions_for_paper(
    db: Session,
    *,
    candidates: list[Question],
    user_id: str,
) -> list[Question]:
    """
    Fair coverage selection for single- and multi-topic papers:

    1. One wording per variant_group (concept)
    2. Prefer not-recently-used (soft cooldown) when the fresh pool is large enough
    3. Otherwise fall back to least-asked cooled questions so creates never starve
    4. Among the chosen priority tier, take least-asked first (topic round-robin)
    5. Shuffle only the final N for student-facing order
    """
    picks = _one_pick_per_variant_group(candidates)
    if not picks:
        return []

    target = _target_paper_size(len(picks))
    if target <= 0:
        return []

    recent_ids = _recent_paper_ids(db, user_id=user_id)
    recent_question_ids = _question_ids_on_papers(db, paper_ids=recent_ids)
    now = datetime.now(timezone.utc)

    fresh: list[Question] = []
    cooled: list[Question] = []
    for q in picks:
        if _is_recently_used(
            q, recent_question_ids=recent_question_ids, now=now
        ):
            cooled.append(q)
        else:
            fresh.append(q)

    # Soft cooldown: use fresh first; only dip into cooled if needed to fill target.
    ordered = _topic_round_robin(fresh)
    if len(ordered) < target:
        ordered.extend(_topic_round_robin(cooled))

    selected = ordered[:target]
    random.shuffle(selected)
    return selected


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

    needs = note.status != NoteStatus.READY.value or not (
        note.canonical_content_en or ""
    ).strip()
    if needs:
        try:
            process_note(db, note_id=note.id)
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.exception("Auto-process failed for note %s", note.id)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to process note: {exc}",
            ) from exc
        note = db.get(Note, note_id)
        if note is None or note.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Note not found"
            )

    if note.status != NoteStatus.READY.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Note could not be prepared for a test. Check the upload and try again.",
        )
    if note.batch_folder_id:
        refresh_topic_canonical(db, batch_folder_id=note.batch_folder_id)
    canonical = (note.canonical_content_en or "").strip()
    if not canonical:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Note has no English canonical content",
        )

    limits = limits_for(user.account_type)
    _enforce_quota(
        db,
        user_id=user.id,
        monthly_limit=limits.paper_monthly_create_limit,
    )

    lang = _resolve_language(user, language)
    if user.preferred_paper_language != lang:
        user.preferred_paper_language = lang
        db.add(user)

    try:
        generated = generate_mcqs_from_notes(
            canonical,
            output_language=lang,
            max_chunks=limits.paper_mcq_max_chunks,
        )
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
                "No eligible questions available for a new test. "
                "Try again later or process richer notes."
            ),
        )

    if note.batch_folder_id:
        batch = db.get(BatchFolder, note.batch_folder_id)
        if batch is not None:
            title = _build_paper_title(db, user_id=user.id, batches=[batch])
        else:
            title = "Test-1"
    else:
        title = "Test-1"

    paper = QuestionPaper(
        id=str(uuid.uuid4()),
        user_id=user.id,
        note_id=note.id,
        batch_folder_id=note.batch_folder_id,
        language=lang,
        status=PaperStatus.READY.value,
        title=title,
        question_count=len(selected),
    )
    db.add(paper)
    db.flush()

    if note.batch_folder_id:
        db.add(
            PaperBatchLink(
                id=str(uuid.uuid4()),
                paper_id=paper.id,
                batch_id=note.batch_folder_id,
            )
        )

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
    return generate_paper_for_batches(
        db,
        user=user,
        batch_ids=[batch_id],
        language=language,
    )


def generate_paper_for_batches(
    db: Session,
    *,
    user: User,
    batch_ids: list[str],
    language: str | None = None,
) -> QuestionPaper:
    """Create one paper from one or more topics; auto-process unprocessed notes first."""
    ids = list(dict.fromkeys(bid for bid in batch_ids if bid))
    if not ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Select at least one topic",
        )

    batches: list[BatchFolder] = []
    exam_id: str | None = None
    for bid in ids:
        batch = db.get(BatchFolder, bid)
        if batch is None or batch.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found",
            )
        if exam_id is None:
            exam_id = batch.exam_id
        elif batch.exam_id != exam_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="All topics must belong to the same exam",
            )
        batches.append(batch)

    notes = list(
        db.scalars(
            select(Note)
            .where(Note.batch_folder_id.in_(ids), Note.user_id == user.id)
            .order_by(Note.created_at.asc())
        ).all()
    )
    if not notes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected topics have no notes. Upload PDFs first.",
        )

    limits = limits_for(user.account_type)
    _enforce_quota(
        db,
        user_id=user.id,
        monthly_limit=limits.paper_monthly_create_limit,
    )

    # Auto-process any note that is not Ready (student never taps Process).
    for note in notes:
        needs = note.status != NoteStatus.READY.value or not (
            note.canonical_content_en or ""
        ).strip()
        if needs:
            try:
                process_note(db, note_id=note.id)
            except HTTPException:
                raise
            except Exception as exc:  # noqa: BLE001
                logger.exception("Auto-process failed for note %s", note.id)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Failed to process note “{note.title}”: {exc}",
                ) from exc

    # Re-load after processing and refresh each topic's joined canonical.
    notes = list(
        db.scalars(
            select(Note)
            .where(Note.batch_folder_id.in_(ids), Note.user_id == user.id)
            .order_by(Note.created_at.asc())
        ).all()
    )
    ready = [
        n
        for n in notes
        if n.status == NoteStatus.READY.value
        and (n.canonical_content_en or "").strip()
    ]
    if not ready:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not prepare notes for a test. Check uploads and try again.",
        )

    for bid in ids:
        refresh_topic_canonical(db, batch_folder_id=bid)

    # Reload batches after canonical refresh
    batches = [db.get(BatchFolder, b.id) for b in batches]
    batches = [b for b in batches if b is not None]

    lang = _resolve_language(user, language)
    if user.preferred_paper_language != lang:
        user.preferred_paper_language = lang
        db.add(user)

    notes_by_batch: dict[str, list[Note]] = defaultdict(list)
    for n in ready:
        if n.batch_folder_id:
            notes_by_batch[n.batch_folder_id].append(n)

    note_ids = [n.id for n in ready]
    primary = ready[0]

    for batch in batches:
        topic_canonical = (batch.canonical_content_en or "").strip()
        if not topic_canonical:
            continue
        topic_notes = notes_by_batch.get(batch.id) or []
        anchor = topic_notes[0] if topic_notes else primary
        try:
            generated = generate_mcqs_from_notes(
                topic_canonical,
                output_language=lang,
                max_chunks=limits.paper_mcq_max_chunks,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("MCQ generation failed for topic %s", batch.id)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to generate MCQs for “{batch.name}”: {exc}",
            ) from exc

        for item in generated:
            options = item["options"]
            question = Question(
                id=str(uuid.uuid4()),
                user_id=user.id,
                note_id=anchor.id,
                variant_group_id=str(item["variant_group_id"])[:36],
                topic=item.get("topic") or batch.name,
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
                "No eligible questions available for a new test. "
                "Try again later or add richer notes."
            ),
        )

    title = _build_paper_title(db, user_id=user.id, batches=batches)

    paper = QuestionPaper(
        id=str(uuid.uuid4()),
        user_id=user.id,
        note_id=primary.id,
        batch_folder_id=batches[0].id,
        language=lang,
        status=PaperStatus.READY.value,
        title=title,
        question_count=len(selected),
    )
    db.add(paper)
    db.flush()

    for batch in batches:
        db.add(
            PaperBatchLink(
                id=str(uuid.uuid4()),
                paper_id=paper.id,
                batch_id=batch.id,
            )
        )

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
