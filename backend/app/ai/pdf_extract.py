"""Local PDF text extraction (no API cost)."""

from __future__ import annotations

import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract plain text from PDF bytes. Raises ValueError if unreadable/empty."""
    try:
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Could not open PDF: {exc}") from exc

    parts: list[str] = []
    try:
        for page in document:
            text = page.get_text("text") or ""
            cleaned = text.strip()
            if cleaned:
                parts.append(cleaned)
    finally:
        document.close()

    joined = "\n\n".join(parts).strip()
    if not joined:
        raise ValueError(
            "No extractable text found. Typed/digital PDFs are required for MVP "
            "(handwritten scans need OCR later)."
        )
    return joined
