"""Unit tests for chunked MCQ generation."""

from __future__ import annotations

import pytest

from app.ai import generate_mcqs


def test_generate_mcqs_calls_openai_per_chunk(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(generate_mcqs.settings, "OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(generate_mcqs.settings, "NOTE_AI_MAX_INPUT_CHARS", 50)
    monkeypatch.setattr(generate_mcqs.settings, "NOTE_AI_CHUNK_OVERLAP", 0)
    monkeypatch.setattr(generate_mcqs.settings, "PAPER_MCQ_MAX_CHUNKS", 10)
    monkeypatch.setattr(generate_mcqs.settings, "PAPER_GENERATE_UNIQUE_TARGET", 8)
    monkeypatch.setattr(generate_mcqs.settings, "PAPER_GENERATE_VARIANTS_PER_CONCEPT", 2)

    calls: list[int] = []

    def _fake_call(**kwargs):
        calls.append(kwargs["chunk_index"])
        idx = kwargs["chunk_index"]
        return [
            {
                "variant_group_id": f"g{idx}",
                "topic": "T",
                "stem": f"Question from chunk {idx}?",
                "options": ["A", "B", "C", "D"],
                "correct_index": 0,
                "explanation": "Because",
            }
        ]

    monkeypatch.setattr(generate_mcqs, "_call_mcq_chunk", _fake_call)

    # Two chunks at max_chars=50
    text = ("Alpha paragraph about equality. " * 3) + ("\n\nBeta paragraph about speech. " * 3)
    items = generate_mcqs.generate_mcqs_from_notes(text, output_language="en")
    assert len(calls) >= 2
    assert len(items) == len(calls)
    assert items[0]["stem"].startswith("Question from chunk")


def test_generate_mcqs_respects_max_chunks_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(generate_mcqs.settings, "OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(generate_mcqs.settings, "NOTE_AI_MAX_INPUT_CHARS", 20)
    monkeypatch.setattr(generate_mcqs.settings, "NOTE_AI_CHUNK_OVERLAP", 0)

    calls: list[int] = []

    def _fake_call(**kwargs):
        calls.append(kwargs["chunk_index"])
        return [
            {
                "variant_group_id": f"g{kwargs['chunk_index']}",
                "topic": "T",
                "stem": f"Q{kwargs['chunk_index']}?",
                "options": ["A", "B", "C", "D"],
                "correct_index": 0,
                "explanation": None,
            }
        ]

    monkeypatch.setattr(generate_mcqs, "_call_mcq_chunk", _fake_call)

    text = "word " * 200
    items = generate_mcqs.generate_mcqs_from_notes(text, output_language="en", max_chunks=2)
    assert len(calls) == 2
    assert len(items) == 2
