"""Exam catalog (popular + user-added shared list)."""

from __future__ import annotations

import re
import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Exam, ExamCatalogItem

_POPULAR = [
    ("UPSC Civil Services", "UPSC"),
    ("SSC CGL", "SSC"),
    ("IBPS PO", "IBPS"),
    ("NEET UG", "NEET"),
    ("JEE Main", "JEE"),
    ("GATE", "GATE"),
    ("CAT", "CAT"),
    ("RRB NTPC", "RRB"),
    ("State PSC", "PSC"),
    ("NDA", "NDA"),
]


def _badge_from_name(name: str) -> str:
    cleaned = name.strip()
    parts = re.split(r"\s+", cleaned)
    if len(parts) == 1:
        return cleaned[:8].upper()
    return "".join(p[0] for p in parts if p)[:8].upper()


def seed_popular_exams(db: Session) -> None:
    for name, badge in _POPULAR:
        existing = db.scalar(
            select(ExamCatalogItem).where(
                func.lower(ExamCatalogItem.name) == name.lower()
            )
        )
        if existing is None:
            db.add(
                ExamCatalogItem(
                    id=str(uuid.uuid4()),
                    name=name,
                    badge=badge,
                    is_popular=1,
                    created_by_user_id=None,
                )
            )
    db.commit()


def list_catalog(db: Session, *, query: str | None = None) -> list[ExamCatalogItem]:
    stmt = select(ExamCatalogItem).order_by(
        ExamCatalogItem.is_popular.desc(),
        ExamCatalogItem.name.asc(),
    )
    q = (query or "").strip()
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(func.lower(ExamCatalogItem.name).like(like))
    return list(db.scalars(stmt).all())


def add_catalog_item(
    db: Session,
    *,
    user_id: str,
    name: str,
) -> ExamCatalogItem:
    cleaned = name.strip()
    if not cleaned:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exam name is required",
        )
    existing = db.scalar(
        select(ExamCatalogItem).where(
            func.lower(ExamCatalogItem.name) == cleaned.lower()
        )
    )
    if existing is not None:
        return existing
    item = ExamCatalogItem(
        id=str(uuid.uuid4()),
        name=cleaned[:255],
        badge=_badge_from_name(cleaned),
        is_popular=0,
        created_by_user_id=user_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def ensure_user_exams_from_catalog(
    db: Session,
    *,
    user_id: str,
    catalog_ids: list[str],
    custom_names: list[str],
) -> list[Exam]:
    selected_ids = list(dict.fromkeys(catalog_ids))
    created: list[Exam] = []

    for cid in selected_ids:
        item = db.get(ExamCatalogItem, cid)
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Catalog exam not found: {cid}",
            )
        already = db.scalar(
            select(Exam).where(
                Exam.user_id == user_id,
                or_(
                    Exam.catalog_id == item.id,
                    func.lower(Exam.name) == item.name.lower(),
                ),
            )
        )
        if already is not None:
            created.append(already)
            continue
        exam = Exam(
            id=str(uuid.uuid4()),
            user_id=user_id,
            catalog_id=item.id,
            name=item.name,
            badge=item.badge,
        )
        db.add(exam)
        created.append(exam)

    for raw in custom_names:
        item = add_catalog_item(db, user_id=user_id, name=raw)
        already = db.scalar(
            select(Exam).where(
                Exam.user_id == user_id,
                or_(
                    Exam.catalog_id == item.id,
                    func.lower(Exam.name) == item.name.lower(),
                ),
            )
        )
        if already is not None:
            if already not in created:
                created.append(already)
            continue
        exam = Exam(
            id=str(uuid.uuid4()),
            user_id=user_id,
            catalog_id=item.id,
            name=item.name,
            badge=item.badge,
        )
        db.add(exam)
        created.append(exam)

    if not created and not selected_ids and not custom_names:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Select or add at least one exam",
        )

    db.commit()
    for exam in created:
        db.refresh(exam)
    return created
