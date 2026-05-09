"""
app/config/settings.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    Every production app needs ONE canonical place where environment variables
    are read, validated, and typed.  Pydantic-Settings gives us:
      - Automatic .env loading
      - Type coercion  (string "true" → bool True)
      - Validation at startup — the server won't start if a required var is missing
      - IDE auto-completion via Python types

WHAT IT DOES
    Defines a `Settings` class (subclassing Pydantic BaseSettings) that maps
    every environment variable to a typed Python attribute.
    A module-level `get_settings()` function cached with `@lru_cache` ensures
    the .env file is parsed only once regardless of how many modules import it.

HOW IT CONNECTS
    Imported by:
      - app/db/session.py       → DATABASE_URL
      - app/main.py             → APP_NAME, DEBUG, ALLOWED_ORIGINS, API_V1_PREFIX
      - app/core/logging.py     → LOG_LEVEL
"""

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Model config ─────────────────────────────────────────────────────────
    model_config = SettingsConfigDict(
        env_file=".env",          # Look for .env in the working directory
        env_file_encoding="utf-8",
        case_sensitive=False,     # DATABASE_URL == database_url
        extra="ignore",           # Silently ignore unknown env vars
    )

    # ── Application ──────────────────────────────────────────────────────────
    app_env: str = "development"
    app_name: str = "Agentic Task Router"
    app_version: str = "0.1.0"
    debug: bool = True
    secret_key: str = "changeme"

    # ── API ───────────────────────────────────────────────────────────────────
    api_v1_prefix: str = "/api/v1"
    # ALLOWED_ORIGINS is a comma-separated string in .env; parsed into a list below
    allowed_origins: str = "http://localhost:3000"
    frontend_url: str = "http://localhost:3000"

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/agentic_router"
    )

    # ── Logging ───────────────────────────────────────────────────────────────
    log_level: str = "INFO"

    # ── AI / OpenAI / Gemini ──────────────────────────────────────────────────
    openai_api_key: str = ""  # Loaded from OPENAI_API_KEY env var
    openai_model_name: str = "gpt-4o-mini" # Default model
    
    gemini_api_key: str = "" # Loaded from GEMINI_API_KEY env var
    gemini_model_name: str = "gemini-2.0-flash" # Default Gemini model
    
    groq_api_key: str = "" # Loaded from GROQ_API_KEY env var
    groq_model_name: str = "llama-3.3-70b-versatile" # Default Groq model

    # ── Redis & Celery ────────────────────────────────────────────────────────
    redis_host: str = "localhost"
    redis_port: int = 6379
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # ── Derived helpers ──────────────────────────────────────────────────────
    @property
    def cors_origins(self) -> List[str]:
        """Split the comma-separated ALLOWED_ORIGINS string into a list."""
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    # ── Validators ────────────────────────────────────────────────────────────
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return upper


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return a cached Settings instance.

    Using @lru_cache means the .env file is read exactly once per process
    lifetime, regardless of how many modules call get_settings().
    FastAPI's Depends() system will also benefit from this caching.
    """
    return Settings()
