"""Lightweight column adds for local Postgres (no Alembic yet)."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine


_NOTE_COLUMNS: list[tuple[str, str]] = [
    ("raw_extracted_text", "TEXT"),
    ("canonical_content_en", "TEXT"),
    ("source_language", "VARCHAR(16)"),
    ("error_message", "TEXT"),
    ("processed_at", "TIMESTAMPTZ"),
]


def ensure_note_processing_columns(engine: Engine) -> None:
    """Add Phase 3 Note columns if missing (Postgres + SQLite)."""
    dialect = engine.dialect.name
    with engine.begin() as conn:
        for name, sql_type in _NOTE_COLUMNS:
            if dialect == "postgresql":
                conn.execute(
                    text(
                        f"ALTER TABLE notes ADD COLUMN IF NOT EXISTS {name} {sql_type}"
                    )
                )
            elif dialect == "sqlite":
                rows = conn.execute(text("PRAGMA table_info(notes)")).fetchall()
                existing = {row[1] for row in rows}
                if name not in existing:
                    # SQLite has no TIMESTAMPTZ; use TEXT-compatible DATETIME
                    sqlite_type = "TEXT" if sql_type == "TIMESTAMPTZ" else sql_type
                    conn.execute(
                        text(f"ALTER TABLE notes ADD COLUMN {name} {sqlite_type}")
                    )
