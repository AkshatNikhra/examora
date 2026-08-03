"""Resolve per-account processing / paper limits from Settings + account_type.

Tier ladder (base env = USER):
  USER ≈ TESTER (real-world student) < DEV < ADMIN
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings
from app.models import AccountType


@dataclass(frozen=True)
class AccountLimits:
    ocr_max_pages: int
    note_ai_max_chunks: int
    paper_monthly_create_limit: int
    paper_max_pages: int
    paper_mcq_max_chunks: int


def normalize_account_type(account_type: str | AccountType | None) -> AccountType:
    raw = (
        account_type.value
        if isinstance(account_type, AccountType)
        else (account_type or AccountType.USER.value)
    )
    try:
        return AccountType(str(raw).strip().upper())
    except ValueError:
        return AccountType.USER


def _pick(
    account_type: AccountType,
    *,
    base: int,
    admin: int,
    dev: int,
    tester: int,
) -> int:
    if account_type is AccountType.ADMIN:
        return max(1, admin)
    if account_type is AccountType.DEV:
        return max(1, dev)
    if account_type is AccountType.TESTER:
        return max(1, tester)
    return max(1, base)


def limits_for(account_type: str | AccountType | None) -> AccountLimits:
    """Return env-backed limits for the given account type (USER = base env)."""
    t = normalize_account_type(account_type)
    return AccountLimits(
        ocr_max_pages=_pick(
            t,
            base=settings.OCR_MAX_PAGES,
            admin=settings.OCR_MAX_PAGES_ADMIN,
            dev=settings.OCR_MAX_PAGES_DEV,
            tester=settings.OCR_MAX_PAGES_TESTER,
        ),
        note_ai_max_chunks=_pick(
            t,
            base=settings.NOTE_AI_MAX_CHUNKS,
            admin=settings.NOTE_AI_MAX_CHUNKS_ADMIN,
            dev=settings.NOTE_AI_MAX_CHUNKS_DEV,
            tester=settings.NOTE_AI_MAX_CHUNKS_TESTER,
        ),
        paper_monthly_create_limit=_pick(
            t,
            base=settings.PAPER_MONTHLY_CREATE_LIMIT,
            admin=settings.PAPER_MONTHLY_CREATE_LIMIT_ADMIN,
            dev=settings.PAPER_MONTHLY_CREATE_LIMIT_DEV,
            tester=settings.PAPER_MONTHLY_CREATE_LIMIT_TESTER,
        ),
        paper_max_pages=_pick(
            t,
            base=settings.PAPER_MAX_PAGES,
            admin=settings.PAPER_MAX_PAGES_ADMIN,
            dev=settings.PAPER_MAX_PAGES_DEV,
            tester=settings.PAPER_MAX_PAGES_TESTER,
        ),
        paper_mcq_max_chunks=_pick(
            t,
            base=settings.PAPER_MCQ_MAX_CHUNKS,
            admin=settings.PAPER_MCQ_MAX_CHUNKS_ADMIN,
            dev=settings.PAPER_MCQ_MAX_CHUNKS_DEV,
            tester=settings.PAPER_MCQ_MAX_CHUNKS_TESTER,
        ),
    )
