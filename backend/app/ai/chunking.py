"""Split long note text into overlapping chunks for LLM calls."""

from __future__ import annotations


def split_text_into_chunks(
    text: str,
    *,
    max_chars: int,
    overlap: int = 200,
) -> list[str]:
    """
    Split text into chunks of at most max_chars, preferring paragraph breaks.
    Small overlap keeps context at boundaries.
    """
    cleaned = text.strip()
    if not cleaned:
        return []
    if max_chars <= 0 or len(cleaned) <= max_chars:
        return [cleaned]

    overlap = max(0, min(overlap, max_chars // 4))
    chunks: list[str] = []
    start = 0
    length = len(cleaned)

    while start < length:
        end = min(start + max_chars, length)
        if end < length:
            window = cleaned[start:end]
            # Prefer break at paragraph, then sentence, then whitespace
            split_at = max(
                window.rfind("\n\n"),
                window.rfind("\n"),
                window.rfind(". "),
                window.rfind(" "),
            )
            if split_at >= max_chars // 3:
                end = start + split_at + 1
        piece = cleaned[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= length:
            break
        start = max(end - overlap, start + 1)

    return chunks
