"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """Typed settings loaded from the backend/.env file."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    ANTHROPIC_API_KEY: str = Field(default="")
    VOYAGE_API_KEY: str = Field(default="")

    SUPABASE_URL: str = Field(default="")
    SUPABASE_ANON_KEY: str = Field(default="")
    SUPABASE_SERVICE_ROLE_KEY: str = Field(default="")
    SUPABASE_SCHEMA: str = Field(default="frontline")

    DEV_COMPANY_ID: str = Field(default="")
    ALLOW_DEV_COMPANY_FALLBACK: bool = Field(default=False)

    SSO_SHARED_SECRET: str = Field(default="")
    FRONTLINE_SESSION_SECRET: str = Field(default="")
    KV_REST_API_URL: str = Field(default="")
    KV_REST_API_TOKEN: str = Field(default="")

    FRONTEND_URL: str = Field(default="*")

    CHAT_RATE_LIMIT: str = Field(default="20/minute")
    TRUST_PROXY_HEADERS: bool = Field(default=False)

    LOG_LEVEL: str = Field(default="INFO")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
