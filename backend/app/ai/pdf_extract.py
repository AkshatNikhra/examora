"""Local PDF text extraction (no API cost)."""

from __future__ import annotations

import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract plain text from PDF bytes. Returns empty string if none found."""
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

    return "\n\n".join(parts).strip()


def pdf_page_count(pdf_bytes: bytes) -> int:
    try:
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Could not open PDF: {exc}") from exc
    try:
        return document.page_count
    finally:
        document.close()


def render_pdf_pages_as_png(
    pdf_bytes: bytes,
    *,
    max_pages: int,
    dpi: int = 150,
) -> list[bytes]:
    """Render up to max_pages of a PDF as PNG bytes for OCR."""
    try:
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Could not open PDF: {exc}") from exc

    images: list[bytes] = []
    try:
        limit = min(document.page_count, max(1, max_pages))
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        for index in range(limit):
            page = document.load_page(index)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            images.append(pix.tobytes("png"))
    finally:
        document.close()
    return images
