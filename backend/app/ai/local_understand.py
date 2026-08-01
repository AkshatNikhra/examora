"""$0 note understanding — cleanup only, no LLM calls."""

from __future__ import annotations

import re


def understand_notes_local(
    raw_text: str,
    *,
    declared_language: str = "en",
    max_chars: int | None = None,
) -> tuple[str, str | None]:
    """
    Produce English-ready canonical study text without an API.

    Cleans the full extract (no silent head-only truncate). Optional max_chars
    is only a hard safety limit for pathological inputs.
    """
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"(?m)^\s*\d+\s*$", "", text)
    text = re.sub(r"(?i)page\s+\d+(\s+of\s+\d+)?", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    if not text:
        raise ValueError("Extracted text was empty after cleanup")

    # Very large safety ceiling only — prefer full document
    safety = max_chars if max_chars is not None else 500_000
    if len(text) > safety:
        text = text[:safety].rsplit("\n", 1)[0].strip() or text[:safety]

    source_language = (declared_language or "en").strip().lower()[:16] or "en"
    return text, source_language
