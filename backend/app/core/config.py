"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "Examora API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/examora"

    CORS_ORIGINS: str = "*"

    FIREBASE_PROJECT_ID: str = "examora-de022"
    FIREBASE_CREDENTIALS_PATH: str = "firebase-service-account.json"

    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = "examora-notes"
    R2_ENDPOINT: str = ""

    # Phone-scanned PDFs often exceed 20 MB; keep in sync with any reverse-proxy body limit.
    MAX_PDF_SIZE_BYTES: int = 100 * 1024 * 1024  # 100 MB

    # V2 — in-app camera / image_picker capture limits (mobile uses these when building PDF).
    # Target ~720p; exact device size may vary — always downscale + JPEG compress before PDF.
    NOTE_IMAGE_MAX_WIDTH: int = 1280
    NOTE_IMAGE_MAX_HEIGHT: int = 720
    NOTE_IMAGE_QUALITY: int = 75  # JPEG quality 1–100

    # Phase 3 — AI understand. Base = USER ≈ TESTER (real-world); overrides for DEV/ADMIN.
    NOTE_AI_PROVIDER: str = "openai"
    # False = upload only stores PDF; process when creating a practice paper (Phase 4)
    NOTE_AUTO_PROCESS: bool = False
    # Max chars per LLM request
    NOTE_AI_MAX_INPUT_CHARS: int = 12000
    NOTE_AI_MAX_OUTPUT_TOKENS: int = 2500
    NOTE_AI_CHUNK_OVERLAP: int = 200
    # USER base matches TESTER; raise via account_type for DEV/ADMIN only.
    NOTE_AI_MAX_CHUNKS: int = 20
    NOTE_AI_MAX_CHUNKS_ADMIN: int = 200
    NOTE_AI_MAX_CHUNKS_DEV: int = 50
    NOTE_AI_MAX_CHUNKS_TESTER: int = 20
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    # Phase 3b — OCR when local PDF text is missing/weak
    GCP_VISION_CREDENTIALS_PATH: str = "gcp-vision-service-account.json"
    OCR_PROVIDER: str = "google_vision"  # google_vision | none
    OCR_MIN_TEXT_CHARS: int = 100
    # OCR safety ceiling (not a student-facing create/upload page cap).
    OCR_MAX_PAGES: int = 500
    OCR_MAX_PAGES_ADMIN: int = 1000
    OCR_MAX_PAGES_DEV: int = 500
    OCR_MAX_PAGES_TESTER: int = 500

    # Phase 4 — paper generation. USER = student product; TESTER slightly higher for QA.
    # Concurrent create slots (USER=4). Each create occupies a slot for PAPER_CREATE_WINDOW_DAYS
    # from that paper's created_at (rolling restore — not calendar-month reset).
    PAPER_MONTHLY_CREATE_LIMIT: int = 4
    PAPER_MONTHLY_CREATE_LIMIT_ADMIN: int = 100
    PAPER_MONTHLY_CREATE_LIMIT_DEV: int = 100
    PAPER_MONTHLY_CREATE_LIMIT_TESTER: int = 20
    PAPER_CREATE_WINDOW_DAYS: int = 30
    # Retained for account-tier tooling / future use — not enforced on upload or create.
    PAPER_MAX_PAGES: int = 500
    PAPER_MAX_PAGES_ADMIN: int = 1000
    PAPER_MAX_PAGES_DEV: int = 500
    PAPER_MAX_PAGES_TESTER: int = 500
    PAPER_SIZE_RATIO: float = 0.3
    PAPER_MIN_QUESTIONS: int = 5
    # Safety ceiling only — paper length is primarily max(MIN, floor(available * RATIO)).
    # Keep this high so a large pool is not clipped early (old default of 15 was too low).
    PAPER_MAX_QUESTIONS: int = 100
    # Soft cooldown preference only (not a hard ban). Prefer questions not used on the
    # last N papers / within D days; fall back to least-asked if the fresh pool is small.
    PAPER_COOLDOWN_DAYS: int = 14
    PAPER_COOLDOWN_GENERATIONS: int = 2
    # Concepts requested per create (spread across MCQ chunks). Pool size drives the 30% paper length.
    PAPER_GENERATE_UNIQUE_TARGET: int = 40
    PAPER_GENERATE_VARIANTS_PER_CONCEPT: int = 2
    # Cap OpenAI MCQ calls when topic canonical is long (same chunk size as NOTE_AI_MAX_INPUT_CHARS).
    PAPER_MCQ_MAX_CHUNKS: int = 20
    PAPER_MCQ_MAX_CHUNKS_ADMIN: int = 200
    PAPER_MCQ_MAX_CHUNKS_DEV: int = 50
    PAPER_MCQ_MAX_CHUNKS_TESTER: int = 20

    @property
    def cors_origins_list(self) -> list[str]:
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def r2_endpoint(self) -> str:
        if self.R2_ENDPOINT.strip():
            return self.R2_ENDPOINT.strip()
        if self.R2_ACCOUNT_ID.strip():
            return f"https://{self.R2_ACCOUNT_ID.strip()}.r2.cloudflarestorage.com"
        return ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
