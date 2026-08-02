"""Pydantic schemas for API responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    phone: str
    full_name: str | None = None
    date_of_birth: str | None = None
    preferred_paper_language: str | None = None
    onboarding_completed: bool = False
    created_at: datetime

    @classmethod
    def from_user(cls, user: object) -> "UserResponse":
        return cls(
            id=user.id,  # type: ignore[attr-defined]
            phone=user.phone,  # type: ignore[attr-defined]
            full_name=getattr(user, "full_name", None),
            date_of_birth=getattr(user, "date_of_birth", None),
            preferred_paper_language=getattr(user, "preferred_paper_language", None),
            onboarding_completed=bool(getattr(user, "onboarding_completed", 0)),
            created_at=user.created_at,  # type: ignore[attr-defined]
        )


class UserPreferenceUpdate(BaseModel):
    preferred_paper_language: str = Field(..., pattern="^(en|hi)$")


class PhoneAccountStatusResponse(BaseModel):
    has_account: bool


class OnboardingProfileRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    date_of_birth: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    preferred_paper_language: str = Field(..., pattern="^(en|hi)$")


class OnboardingExamsRequest(BaseModel):
    catalog_ids: list[str] = Field(default_factory=list)
    custom_names: list[str] = Field(default_factory=list)


class ExamCatalogItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    badge: str
    is_popular: bool = False


class ExamCatalogCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


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
    batch_folder_id: str | None = None

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
            batch_folder_id=getattr(note, "batch_folder_id", None),
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


class GenerateFromTopicsRequest(BaseModel):
    batch_ids: list[str] = Field(..., min_length=1)
    language: str | None = Field(
        default=None,
        description="en or hi; required if user has no preferred_paper_language",
    )


class PaperQuestionResponse(BaseModel):
    """Paper question for attempt UI — answers omitted until submit."""

    id: str
    order_index: int
    stem: str
    options: list[str]
    topic: str | None = None
    variant_group_id: str
    # Only present on attempt review responses
    correct_index: int | None = None
    explanation: str | None = None


class PaperSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    note_id: str | None = None
    batch_folder_id: str | None = None
    title: str
    language: str
    status: str
    question_count: int
    created_at: datetime


class TestTopicFolderResponse(BaseModel):
    topic_id: str
    topic_name: str
    latest_test_at: datetime
    test_count: int
    tests: list[PaperSummaryResponse]


class PaperDetailResponse(PaperSummaryResponse):
    questions: list[PaperQuestionResponse]


class AttemptAnswerSubmit(BaseModel):
    question_id: str
    selected_index: int = Field(..., ge=0, le=3)


class AttemptSubmitRequest(BaseModel):
    answers: list[AttemptAnswerSubmit] = Field(..., min_length=1)


class AttemptAnswerReview(BaseModel):
    question_id: str
    order_index: int
    stem: str
    options: list[str]
    selected_index: int
    correct_index: int
    is_correct: bool
    explanation: str | None = None
    topic: str | None = None


class AttemptResponse(BaseModel):
    id: str
    paper_id: str
    correct_count: int
    total_count: int
    score_percent: int
    submitted_at: datetime
    answers: list[AttemptAnswerReview]


class ExamCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class ExamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    created_at: datetime
    batch_count: int = 0
    badge: str | None = None


class BatchFolderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class BatchFolderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    exam_id: str
    name: str
    created_at: datetime
    note_count: int = 0
    has_paper: bool = False
    page_count_estimate: int | None = None


class ExamUploadHintResponse(BaseModel):
    suggest_new_batch: bool
    reason: str | None = None
    batches_with_papers: list[str] = Field(default_factory=list)


class HomeActivityItem(BaseModel):
    kind: str
    title: str
    subtitle: str | None = None
    at: datetime


class HomeSummaryResponse(BaseModel):
    full_name: str | None = None
    exams_count: int = 0
    tests_taken: int = 0
    avg_score_percent: int | None = None
    exams: list[ExamResponse] = Field(default_factory=list)
    recent_activity: list[HomeActivityItem] = Field(default_factory=list)
