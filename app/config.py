"""Application settings, loaded from environment / `.env` via pydantic-settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── Database ──────────────────────────────────────────────────────────────
    # Production: PostgreSQL via asyncpg. SQLite (aiosqlite) is fine for a first
    # local run and is what the test-suite uses, but Postgres is the target.
    database_url: str = "sqlite+aiosqlite:///./poryadok.db"

    # ── Auth (P0: a single hard-coded user, seeded from these) ────────────────
    auth_email: str = "demo@poryadok.app"
    auth_password: str = "poryadok"
    jwt_secret: str = "dev-insecure-secret-change-me-please-32b+"
    jwt_algorithm: str = "HS256"
    jwt_expire_days: int = 30

    # ── CORS ──────────────────────────────────────────────────────────────────
    cors_origins: str = "*"

    # ── Client-cooling thresholds (P1) ────────────────────────────────────────
    cooling_warm_days: int = 7
    cooling_cold_days: int = 21

    # ── Nightly recompute job (P1) ────────────────────────────────────────────
    scheduler_enabled: bool = True
    digest_hour: int = 7  # local hour to recompute cooling / prepare digests

    # ── Telegram + Claude capture (P2) ────────────────────────────────────────
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    telegram_bot_token: str | None = None
    telegram_allowed_user_ids: str = ""  # comma-separated Telegram user ids (whitelist)
    telegram_webhook_secret: str | None = None  # X-Telegram-Bot-Api-Secret-Token
    router_model: str = "claude-sonnet-4-6"  # cheap model for intent routing (brief §7)
    whisper_model: str = "whisper-1"

    @field_validator("database_url")
    @classmethod
    def _ensure_async_driver(cls, v: str) -> str:
        """Managed hosts (Railway/Render/Heroku) hand out `postgres://` /
        `postgresql://` URLs; rewrite them to the asyncpg driver we use."""
        if v.startswith("postgres://"):
            return "postgresql+asyncpg://" + v[len("postgres://") :]
        if v.startswith("postgresql://"):
            return "postgresql+asyncpg://" + v[len("postgresql://") :]
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def telegram_enabled(self) -> bool:
        return bool(self.telegram_bot_token)

    @property
    def allowed_telegram_ids(self) -> set[int]:
        out: set[int] = set()
        for part in self.telegram_allowed_user_ids.split(","):
            part = part.strip()
            if part:
                try:
                    out.add(int(part))
                except ValueError:
                    pass
        return out


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor (one instance per process)."""
    return Settings()
