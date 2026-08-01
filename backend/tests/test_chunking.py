"""Unit tests for note text chunking."""

from app.ai.chunking import split_text_into_chunks


def test_short_text_single_chunk() -> None:
    assert split_text_into_chunks("hello notes", max_chars=100) == ["hello notes"]


def test_long_text_covers_full_document() -> None:
    # 3 "paragraphs" that exceed one chunk
    parts = [f"Section {i}. " + ("word " * 80) for i in range(5)]
    text = "\n\n".join(parts)
    chunks = split_text_into_chunks(text, max_chars=400, overlap=40)
    assert len(chunks) >= 2
    # Every original section marker should appear in at least one chunk
    for i in range(5):
        assert any(f"Section {i}." in c for c in chunks)


def test_empty_text() -> None:
    assert split_text_into_chunks("   ", max_chars=100) == []
