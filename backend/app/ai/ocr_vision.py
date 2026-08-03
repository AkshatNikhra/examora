"""Google Cloud Vision OCR for handwritten / scanned PDF pages."""

from __future__ import annotations

import logging
from pathlib import Path

from app.ai.pdf_extract import render_pdf_pages_as_png
from app.core.config import settings

logger = logging.getLogger(__name__)


def _credentials_path() -> Path:
    raw = (settings.GCP_VISION_CREDENTIALS_PATH or "").strip()
    if not raw:
        raise ValueError(
            "GCP_VISION_CREDENTIALS_PATH is not set. "
            "Save your Vision service account JSON and set the path in backend/.env"
        )
    path = Path(raw)
    if not path.is_absolute():
        # Resolve relative to backend working directory
        path = Path.cwd() / path
    if not path.is_file():
        raise ValueError(f"Vision credentials file not found: {path}")
    return path


def ocr_pdf_with_vision(pdf_bytes: bytes, *, max_pages: int | None = None) -> str:
    """
    OCR a PDF via Cloud Vision DOCUMENT_TEXT_DETECTION.
    Renders each page locally, then sends images to Vision (billed per page).
    """
    from google.cloud import vision
    from google.oauth2 import service_account

    page_limit = max_pages if max_pages is not None else settings.OCR_MAX_PAGES
    page_limit = max(1, page_limit)

    images = render_pdf_pages_as_png(pdf_bytes, max_pages=page_limit)
    if not images:
        raise ValueError("PDF has no pages to OCR")

    credentials = service_account.Credentials.from_service_account_file(
        str(_credentials_path())
    )
    client = vision.ImageAnnotatorClient(credentials=credentials)

    parts: list[str] = []
    for index, png in enumerate(images, start=1):
        image = vision.Image(content=png)
        response = client.document_text_detection(image=image)
        if response.error.message:
            raise ValueError(
                f"Vision OCR failed on page {index}: {response.error.message}"
            )
        text = ""
        if response.full_text_annotation and response.full_text_annotation.text:
            text = response.full_text_annotation.text.strip()
        if text:
            parts.append(text)
        logger.info("Vision OCR page %s/%s: %s chars", index, len(images), len(text))

    joined = "\n\n".join(parts).strip()
    if not joined:
        raise ValueError(
            "OCR found no readable text. Try clearer photos/scans "
            "(Hindi/English handwriting, good lighting)."
        )
    return joined
