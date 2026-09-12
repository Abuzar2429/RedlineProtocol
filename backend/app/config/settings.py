from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.
    All settings have safe development defaults except secrets.
    """

    # ── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = "AI Governance Crisis Simulator"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # ── Server ───────────────────────────────────────────────────────────────
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/crisis_simulator"

    # ── CORS ─────────────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # ── LLM Configuration — Phase 4+ ──────────────────────────────────────────
    LLM_PROVIDER: str = "mock"       # "mock" | "anthropic" | "openai"
    LLM_MODEL: str = "claude-sonnet-4-6"
    LLM_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""      # Alias / backwards compatibility
    LLM_TEMPERATURE: float = 0.7
    LLM_TIMEOUT: float = 30.0        # Seconds
    LLM_MAX_RETRIES: int = 1

    # ── Coordinator LLM Configuration — Phase 5 ───────────────────────────────
    COORDINATOR_MODEL: str = "claude-sonnet-4-6"
    COORDINATOR_TEMPERATURE: float = 0.3

    # ── Misc ─────────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
