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

    MAX_PDF_SIZE_BYTES: int = 20 * 1024 * 1024  # 20 MB

    # Phase 3 — cheap AI; full doc = chunk→stitch. Dev: keep NOTE_AI_MAX_CHUNKS=1.
    NOTE_AI_PROVIDER: str = "openai"
    # False = upload only stores PDF; process when creating a practice paper (Phase 4)
    NOTE_AUTO_PROCESS: bool = False
    # Max chars per LLM request
    NOTE_AI_MAX_INPUT_CHARS: int = 12000
    NOTE_AI_MAX_OUTPUT_TOKENS: int = 2500
    NOTE_AI_CHUNK_OVERLAP: int = 200
    # Dev default 1 = first chunk only (cheap). Raise (e.g. 20) for full-document.
    NOTE_AI_MAX_CHUNKS: int = 1
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

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
