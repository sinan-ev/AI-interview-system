"""
Application Configuration Module.
Loads environment variables and validates types using Pydantic Settings.
"""
from functools import lru_cache
from typing import List
from pydantic import Field, AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Core App
    APP_NAME: str = "AI Interview & Assessment Platform"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "dev-secret-key-change-in-production-min-32-chars-long"

    # Database (PostgreSQL + pgvector)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_interview_db"
    SYNC_DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/ai_interview_db"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_ECHO: bool = False

    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Security & JWT Authentication
    JWT_SECRET: str = "dev-jwt-secret-replace-in-production-min-32-chars-abc"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # AI LLM Provider Configuration
    # Supported: "mock", "openai", "anthropic", "google"
    LLM_PROVIDER: str = "mock"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o"
    LLM_TEMPERATURE: float = 0.2
    LLM_MAX_TOKENS: int = 2048

    # Embeddings Configuration
    # Supported: "mock", "openai", "local"
    EMBEDDING_PROVIDER: str = "mock"
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536

    # Speech-to-Text (STT) Provider
    # Supported: "mock", "whisper", "deepgram", "openai"
    STT_PROVIDER: str = "mock"
    STT_API_KEY: str = ""
    STT_MODEL: str = "whisper-1"

    # Storage & Upload Limits
    MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB default
    ALLOWED_FILE_EXTENSIONS: List[str] = ["pdf", "docx", "pptx", "txt", "md"]
    ALLOWED_AUDIO_EXTENSIONS: List[str] = ["wav", "mp3", "m4a", "webm", "ogg"]
    UPLOAD_DIR: str = "./uploads"

    # Rate Limiting
    RATE_LIMIT: str = "100/minute"
    AUTH_RATE_LIMIT: str = "5/minute"
    INTERVIEW_RATE_LIMIT: str = "10/minute"

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]

    # Evaluator & Rubric Versions for reproducible scoring
    EVALUATOR_VERSION: str = "1.0.0"
    RUBRIC_VERSION: str = "1.0.0"
    SCORING_VERSION: str = "1.0.0"


@lru_cache()
def get_settings() -> Settings:
    """Return cached instance of application settings."""
    return Settings()


settings = get_settings()
