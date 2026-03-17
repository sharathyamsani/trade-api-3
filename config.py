"""
Configuration – reads from environment variables with sensible defaults.
Copy .env.example to .env and fill in your API keys.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── API Keys ──────────────────────────────────────────────────────────────
    GEMINI_API_KEY: str = ""          # Required for AI analysis
    SERPER_API_KEY: str = ""          # Optional – richer web search results

    # ── JWT ───────────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "change-me-in-production-super-secret-key-2024"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # ── Rate limiting ─────────────────────────────────────────────────────────
    RATE_LIMIT_REQUESTS: int = 10   # max requests …
    RATE_LIMIT_WINDOW: int = 60     # … per this many seconds

    # ── Cache ─────────────────────────────────────────────────────────────────
    CACHE_TTL_SECONDS: int = 3600   # 1 hour


settings = Settings()
