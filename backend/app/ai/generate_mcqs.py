"""Generate MCQs from English canonical notes (OpenAI)."""

from __future__ import annotations

import json
import re
import uuid
from typing import Any

import httpx

from app.core.config import settings


def _system_prompt(output_language: str, unique_target: int, variants: int) -> str:
    lang_name = "Hindi" if output_language == "hi" else "English"
    return (
        "You create competitive-exam MCQs from study notes.\n"
        f"Write all question stems, options, and explanations in {lang_name}.\n"
        "Rules:\n"
        "- Use ONLY facts present in the notes. Do not invent syllabus content.\n"
        "- Each item must have exactly 4 options and one correct answer.\n"
        "- Cover different topics/headings from the notes when possible.\n"
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


def generate_mcqs_from_notes(
    canonical_content_en: str,
    *,
    output_language: str = "en",
) -> list[dict[str, Any]]:
    if not settings.OPENAI_API_KEY.strip():
        raise ValueError("OPENAI_API_KEY is not configured")

    unique_target = settings.PAPER_GENERATE_UNIQUE_TARGET
    variants = settings.PAPER_GENERATE_VARIANTS_PER_CONCEPT
    clipped = canonical_content_en[: settings.NOTE_AI_MAX_INPUT_CHARS]

    payload: dict[str, Any] = {
        "model": settings.OPENAI_MODEL,
        "temperature": 0.4,
        "max_tokens": 3500,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": _system_prompt(output_language, unique_target, variants),
            },
            {
                "role": "user",
                "content": f"Study notes (English canonical):\n{clipped}",
            },
        ],
    }

    url = f"{settings.OPENAI_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=120.0) as client:
        response = client.post(url, headers=headers, json=payload)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ValueError(
                f"OpenAI MCQ generation failed ({response.status_code}): "
                f"{response.text[:500]}"
            ) from exc
        data = response.json()

    content = data["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    raw_items = parsed.get("questions") or []
    if not isinstance(raw_items, list) or not raw_items:
        raise ValueError("OpenAI returned no questions")

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

    if not cleaned:
        raise ValueError("No valid MCQs after validation")
    return _dedupe_exact_stems(cleaned)


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
