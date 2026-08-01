"""Pydantic schemas for API responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    phone: str
    preferred_paper_language: str | None = None
    created_at: datetime


class UserPreferenceUpdate(BaseModel):
    preferred_paper_language: str = Field(..., pattern="^(en|hi)$")


class NoteResponse(BaseModel):
    """List/summary payload — no full text bodies."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    title: str
    file_url: str
    language: str
    status: str
    source_language: str | None = None
    error_message: str | None = None
    processed_at: datetime | None = None
    created_at: datetime
    has_canonical: bool = False

    @classmethod
    def from_note(cls, note: object) -> "NoteResponse":
        canonical = getattr(note, "canonical_content_en", None)
        return cls(
            id=note.id,  # type: ignore[attr-defined]
            user_id=note.user_id,  # type: ignore[attr-defined]
            title=note.title,  # type: ignore[attr-defined]
            file_url=note.file_url,  # type: ignore[attr-defined]
            language=note.language,  # type: ignore[attr-defined]
            status=note.status,  # type: ignore[attr-defined]
            source_language=getattr(note, "source_language", None),
            error_message=getattr(note, "error_message", None),
            processed_at=getattr(note, "processed_at", None),
            created_at=note.created_at,  # type: ignore[attr-defined]
            has_canonical=bool(canonical and str(canonical).strip()),
        )


class NoteDetailResponse(NoteResponse):
    """Full note including extracted PDF text and English canonical content."""

    raw_extracted_text: str | None = None
    canonical_content_en: str | None = None

    @classmethod
    def from_note(cls, note: object) -> "NoteDetailResponse":
        base = NoteResponse.from_note(note)
        return cls(
            **base.model_dump(),
            raw_extracted_text=getattr(note, "raw_extracted_text", None),
            canonical_content_en=getattr(note, "canonical_content_en", None),
        )


class NoteStatusResponse(BaseModel):
    id: str
    status: str
    source_language: str | None = None
    error_message: str | None = None
    processed_at: datetime | None = None
    has_canonical: bool = False
    canonical_preview: str | None = Field(
        default=None,
        description="First ~240 chars of English canonical content when ready",
    )
    raw_preview: str | None = Field(
        default=None,
        description="First ~240 chars of raw PDF extract when available",
    )


class GeneratePaperRequest(BaseModel):
    language: str | None = Field(
        default=None,
        description="en or hi; required if user has no preferred_paper_language",
    )


class PaperQuestionResponse(BaseModel):
    id: str
    order_index: int
    stem: str
    options: list[str]
    correct_index: int
    explanation: str | None = None
    topic: str | None = None
    variant_group_id: str


class PaperSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    note_id: str
    title: str
    language: str
    status: str
    question_count: int
    created_at: datetime


class PaperDetailResponse(PaperSummaryResponse):
    questions: list[PaperQuestionResponse]
