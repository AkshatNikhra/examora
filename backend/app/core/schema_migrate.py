"""Lightweight column/table ensures for local Postgres (no Alembic yet)."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.core.database import Base


_NOTE_COLUMNS: list[tuple[str, str]] = [
    ("raw_extracted_text", "TEXT"),
    ("canonical_content_en", "TEXT"),
    ("source_language", "VARCHAR(16)"),
    ("error_message", "TEXT"),
    ("processed_at", "TIMESTAMPTZ"),
    ("batch_folder_id", "VARCHAR(36)"),
]

_USER_COLUMNS: list[tuple[str, str]] = [
    ("preferred_paper_language", "VARCHAR(8)"),
]

_PAPER_COLUMNS: list[tuple[str, str]] = [
    ("batch_folder_id", "VARCHAR(36)"),
]


def _add_columns(engine: Engine, table: str, columns: list[tuple[str, str]]) -> None:
    dialect = engine.dialect.name
    with engine.begin() as conn:
        for name, sql_type in columns:
            if dialect == "postgresql":
                conn.execute(
                    text(
                        f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {name} {sql_type}"
                    )
                )
            elif dialect == "sqlite":
                rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
                existing = {row[1] for row in rows}
                if name not in existing:
                    sqlite_type = "TEXT" if sql_type == "TIMESTAMPTZ" else sql_type
                    conn.execute(
                        text(f"ALTER TABLE {table} ADD COLUMN {name} {sqlite_type}")
                    )


def _make_paper_note_id_nullable(engine: Engine) -> None:
    dialect = engine.dialect.name
    if dialect != "postgresql":
        return
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                DO $$
                BEGIN
                  ALTER TABLE question_papers ALTER COLUMN note_id DROP NOT NULL;
                EXCEPTION
                  WHEN others THEN NULL;
                END $$;
                """
            )
        )


def ensure_note_processing_columns(engine: Engine) -> None:
    """Add Phase 3 Note columns if missing (Postgres + SQLite)."""
    _add_columns(engine, "notes", _NOTE_COLUMNS)


def ensure_phase4_schema(engine: Engine) -> None:
    """Add Phase 4+ user column + create paper/question/attempt tables if missing."""
    _add_columns(engine, "users", _USER_COLUMNS)
    Base.metadata.create_all(bind=engine)


def ensure_phase5_schema(engine: Engine) -> None:
    """Create attempt tables if missing (idempotent create_all)."""
    Base.metadata.create_all(bind=engine)


def ensure_phase4b_schema(engine: Engine) -> None:
    """Exam/batch tables + note/paper folder columns."""
    Base.metadata.create_all(bind=engine)
    _add_columns(engine, "notes", [("batch_folder_id", "VARCHAR(36)")])
    _add_columns(engine, "question_papers", _PAPER_COLUMNS)
    _make_paper_note_id_nullable(engine)
