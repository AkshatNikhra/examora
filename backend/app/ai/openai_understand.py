"""Cheap OpenAI path — gpt-4o-mini with full-document chunk + stitch."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.ai.chunking import split_text_into_chunks
from app.core.config import settings

logger = logging.getLogger(__name__)

_SYSTEM = (
    "You are helping Indian competitive-exam students. "
    "Given raw text extracted from study notes (any language), produce clear "
    "English study content suitable for later MCQ generation.\n"
    "Rules:\n"
    "- Keep all important facts, definitions, lists, and section headings.\n"
    "- Remove PDF junk: page numbers, headers/footers, repeated watermarks.\n"
    "- If the notes are not English, translate the meaning into clear English.\n"
    "- Organize with short headings and bullet points where helpful.\n"
    "- Do not invent facts that are not in the notes.\n"
    "- Do not write exam questions yet — only cleaned study content.\n"
    "- This may be one chunk of a longer document — clean this chunk fully; "
    "do not summarize away detail just to be short.\n"
    "Return JSON only with keys:\n"
    '{"canonical_content_en":"string","source_language":"en|hi|other"}'
)


def _call_openai_chunk(
    *,
    chunk_text: str,
    declared_language: str,
    chunk_index: int,
    chunk_total: int,
    max_output_tokens: int,
    client: httpx.Client,
) -> tuple[str, str]:
    payload: dict[str, Any] = {
        "model": settings.OPENAI_MODEL,
        "temperature": 0.2,
        "max_tokens": max_output_tokens,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": _SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Declared note language hint: {declared_language}\n"
                    f"Document chunk {chunk_index} of {chunk_total}.\n\n"
                    f"Raw extracted notes (this chunk):\n{chunk_text}"
                ),
            },
        ],
    }

    url = f"{settings.OPENAI_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    response = client.post(url, headers=headers, json=payload)
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = response.text[:500]
        raise ValueError(
            f"OpenAI request failed on chunk {chunk_index}/{chunk_total} "
            f"({response.status_code}): {detail}"
        ) from exc

    data = response.json()
    content = data["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    canonical = (parsed.get("canonical_content_en") or "").strip()
    if not canonical:
        raise ValueError(
            f"OpenAI returned empty canonical_content_en "
            f"for chunk {chunk_index}/{chunk_total}"
        )
    source = (parsed.get("source_language") or declared_language or "en").strip().lower()
    return canonical, source[:16]


def understand_notes_openai(
    raw_text: str,
    *,
    declared_language: str = "en",
    max_input_chars: int | None = None,
    max_output_tokens: int | None = None,
) -> tuple[str, str | None]:
    if not settings.OPENAI_API_KEY.strip():
        raise ValueError(
            "OPENAI_API_KEY is not configured. Add it to backend/.env "
            "(NOTE_AI_PROVIDER=openai)."
        )

    max_in = max_input_chars or settings.NOTE_AI_MAX_INPUT_CHARS
    max_out = max_output_tokens or settings.NOTE_AI_MAX_OUTPUT_TOKENS
    max_chunks = max(1, settings.NOTE_AI_MAX_CHUNKS)

    chunks = split_text_into_chunks(
        raw_text,
        max_chars=max_in,
        overlap=settings.NOTE_AI_CHUNK_OVERLAP,
    )
    if not chunks:
        raise ValueError("No text to send to OpenAI")

    if len(chunks) > max_chunks:
        logger.warning(
            "Note has %s chunks; capping at NOTE_AI_MAX_CHUNKS=%s",
            len(chunks),
            max_chunks,
        )
        chunks = chunks[:max_chunks]

    total = len(chunks)
    logger.info("Understanding notes with OpenAI in %s chunk(s)", total)

    parts: list[str] = []
    source_language: str | None = None

    with httpx.Client(timeout=120.0) as client:
        for index, chunk in enumerate(chunks, start=1):
            canonical, source = _call_openai_chunk(
                chunk_text=chunk,
                declared_language=declared_language,
                chunk_index=index,
                chunk_total=total,
                max_output_tokens=max_out,
                client=client,
            )
            parts.append(canonical)
            if source_language is None:
                source_language = source

    stitched = "\n\n".join(parts).strip()
    if not stitched:
        raise ValueError("OpenAI returned empty content after stitching chunks")
    return stitched, source_language or (declared_language or "en")[:16]
