"""Generate MCQs from English canonical notes (OpenAI), chunked for long text."""

from __future__ import annotations

import json
import logging
import re
import uuid
from typing import Any

import httpx

from app.ai.chunking import split_text_into_chunks
from app.core.config import settings

logger = logging.getLogger(__name__)


def _system_prompt(
    output_language: str,
    unique_target: int,
    variants: int,
    *,
    chunk_index: int,
    chunk_total: int,
) -> str:
    lang_name = "Hindi" if output_language == "hi" else "English"
    return (
        "You create competitive-exam MCQs from study notes.\n"
        f"Write all question stems, options, and explanations in {lang_name}.\n"
        f"This is chunk {chunk_index} of {chunk_total} of a longer document — "
        "generate questions only from THIS chunk.\n"
        "Rules:\n"
        "- Use ONLY facts present in the notes. Do not invent syllabus content.\n"
        "- Prefer application / inference style over copying a sentence from the notes.\n"
        "- Each item must have exactly 4 options and one correct answer.\n"
        "- Cover different topics/headings from this chunk when possible.\n"
        f"- Produce about {unique_target} distinct concepts (unique variant_group).\n"
        f"- For some concepts, include up to {variants} different wordings "
        "(same variant_group_id, different stems).\n"
        "- Questions in the same variant_group must test the same fact, not unrelated ideas.\n"
        "- Avoid duplicate or near-duplicate stems across different groups.\n"
        "- correct_index is 0..3 for options[0]..options[3].\n"
        "Return JSON only:\n"
        '{"questions":[{"variant_group_id":"uuid-or-short-id","topic":"string",'
        '"stem":"string","options":["A","B","C","D"],"correct_index":0,'
        '"explanation":"string"}]}'
    )


def _parse_questions(content: str) -> list[dict[str, Any]]:
    parsed = json.loads(content)
    raw_items = parsed.get("questions") or []
    if not isinstance(raw_items, list):
        return []

    cleaned: list[dict[str, Any]] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        stem = str(item.get("stem") or "").strip()
        options = item.get("options") or []
        if not stem or not isinstance(options, list) or len(options) != 4:
            continue
        opts = [str(o).strip() for o in options]
        if any(not o for o in opts):
            continue
        try:
            correct = int(item.get("correct_index"))
        except (TypeError, ValueError):
            continue
        if correct < 0 or correct > 3:
            continue
        group = str(item.get("variant_group_id") or "").strip() or str(uuid.uuid4())
        topic = str(item.get("topic") or "").strip() or None
        explanation = str(item.get("explanation") or "").strip() or None
        cleaned.append(
            {
                "variant_group_id": group[:36],
                "topic": (topic[:255] if topic else None),
                "stem": stem,
                "options": opts,
                "correct_index": correct,
                "explanation": explanation,
            }
        )
    return cleaned


def _call_mcq_chunk(
    *,
    chunk_text: str,
    output_language: str,
    unique_target: int,
    variants: int,
    chunk_index: int,
    chunk_total: int,
    client: httpx.Client,
) -> list[dict[str, Any]]:
    payload: dict[str, Any] = {
        "model": settings.OPENAI_MODEL,
        "temperature": 0.4,
        "max_tokens": 3500,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": _system_prompt(
                    output_language,
                    unique_target,
                    variants,
                    chunk_index=chunk_index,
                    chunk_total=chunk_total,
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Study notes chunk {chunk_index}/{chunk_total} "
                    f"(English canonical):\n{chunk_text}"
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
        raise ValueError(
            f"OpenAI MCQ generation failed on chunk {chunk_index}/{chunk_total} "
            f"({response.status_code}): {response.text[:500]}"
        ) from exc

    content = response.json()["choices"][0]["message"]["content"]
    return _parse_questions(content)


def generate_mcqs_from_notes(
    canonical_content_en: str,
    *,
    output_language: str = "en",
    max_chunks: int | None = None,
) -> list[dict[str, Any]]:
    if not settings.OPENAI_API_KEY.strip():
        raise ValueError("OPENAI_API_KEY is not configured")

    text = (canonical_content_en or "").strip()
    if not text:
        raise ValueError("No canonical text to generate MCQs from")

    unique_target = settings.PAPER_GENERATE_UNIQUE_TARGET
    variants = settings.PAPER_GENERATE_VARIANTS_PER_CONCEPT
    chunks_cap = max_chunks if max_chunks is not None else settings.PAPER_MCQ_MAX_CHUNKS
    max_chunks_limit = max(1, chunks_cap)

    chunks = split_text_into_chunks(
        text,
        max_chars=settings.NOTE_AI_MAX_INPUT_CHARS,
        overlap=settings.NOTE_AI_CHUNK_OVERLAP,
    )
    if not chunks:
        raise ValueError("No canonical text to generate MCQs from")

    if len(chunks) > max_chunks_limit:
        logger.warning(
            "MCQ input has %s chunks; capping at max_chunks=%s",
            len(chunks),
            max_chunks_limit,
        )
        chunks = chunks[:max_chunks_limit]

    total = len(chunks)
    # Spread concepts across chunks; keep a useful floor per chunk.
    per_chunk_target = max(4, (unique_target + total - 1) // total)
    logger.info(
        "Generating MCQs with OpenAI in %s chunk(s), ~%s concepts each",
        total,
        per_chunk_target,
    )

    all_items: list[dict[str, Any]] = []
    with httpx.Client(timeout=120.0) as client:
        for index, chunk in enumerate(chunks, start=1):
            items = _call_mcq_chunk(
                chunk_text=chunk,
                output_language=output_language,
                unique_target=per_chunk_target,
                variants=variants,
                chunk_index=index,
                chunk_total=total,
                client=client,
            )
            all_items.extend(items)

    cleaned = _dedupe_exact_stems(all_items)
    if not cleaned:
        raise ValueError("OpenAI returned no valid questions across chunks")
    return cleaned


def _dedupe_exact_stems(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for item in items:
        key = re.sub(r"\s+", " ", item["stem"].lower()).strip()
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out
