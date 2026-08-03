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

    # Phase 3 — cheap AI; full doc = chunk→stitch. Dev: keep NOTE_AI_MAX_CHUNKS=1.
    NOTE_AI_PROVIDER: str = "openai"
    # False = upload only stores PDF; process when creating a practice paper (Phase 4)
    NOTE_AUTO_PROCESS: bool = False
    # Max chars per LLM request
    NOTE_AI_MAX_INPUT_CHARS: int = 12000
    NOTE_AI_MAX_OUTPUT_TOKENS: int = 2500
    NOTE_AI_CHUNK_OVERLAP: int = 200
    # Dev default 1 = first chunk only (cheap). Raise (e.g. 20) for full-document.
    # USER uses base; ADMIN/DEV/TESTER use tier overrides via limits_for().
    NOTE_AI_MAX_CHUNKS: int = 1
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
    OCR_MAX_PAGES: int = 20
    OCR_MAX_PAGES_ADMIN: int = 1000
    OCR_MAX_PAGES_DEV: int = 100
    OCR_MAX_PAGES_TESTER: int = 50

    # Phase 4 — paper generation (keep small while developing)
    PAPER_MONTHLY_CREATE_LIMIT: int = 4
    PAPER_MONTHLY_CREATE_LIMIT_ADMIN: int = 10000
    PAPER_MONTHLY_CREATE_LIMIT_DEV: int = 100
    PAPER_MONTHLY_CREATE_LIMIT_TESTER: int = 20
    PAPER_MAX_PAGES: int = 20
    PAPER_MAX_PAGES_ADMIN: int = 1000
    PAPER_MAX_PAGES_DEV: int = 100
    PAPER_MAX_PAGES_TESTER: int = 50
    PAPER_SIZE_RATIO: float = 0.3
    PAPER_MIN_QUESTIONS: int = 5
    PAPER_MAX_QUESTIONS: int = 15
    PAPER_COOLDOWN_DAYS: int = 14
    PAPER_COOLDOWN_GENERATIONS: int = 2
    # How many unique concepts to ask the model to generate per create (cheap)
    PAPER_GENERATE_UNIQUE_TARGET: int = 12
    PAPER_GENERATE_VARIANTS_PER_CONCEPT: int = 2

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
