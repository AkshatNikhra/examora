"""Facade for note understanding providers."""

from __future__ import annotations

from app.ai.local_understand import understand_notes_local
from app.core.config import settings


def understand_notes(
    raw_text: str,
    *,
    declared_language: str = "en",
) -> tuple[str, str | None]:
    provider = (settings.NOTE_AI_PROVIDER or "local").strip().lower()
    if provider == "openai":
        from app.ai.openai_understand import understand_notes_openai

        return understand_notes_openai(
            raw_text,
            declared_language=declared_language,
        )
    return understand_notes_local(
        raw_text,
        declared_language=declared_language,
    )
