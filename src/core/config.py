"""
Config — Single Responsibility Principle (SRP)
This module only manages configuration. Nothing else.
Uses Pydantic BaseSettings for type-safe env loading.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """
    Centralized config. All env vars typed and validated here.
    Dependency Inversion: other modules receive Settings, not os.environ directly.
    """

    # ── LLM ──────────────────────────────────────────────────────────────────
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")

    # ── GitHub ────────────────────────────────────────────────────────────────
    github_token: str = Field(default="", alias="GITHUB_TOKEN")
    github_org: str = Field(default="my-org", alias="GITHUB_ORG")

    # ── Slack ─────────────────────────────────────────────────────────────────
    slack_bot_token: str = Field(default="", alias="SLACK_BOT_TOKEN")
    slack_signing_secret: str = Field(default="", alias="SLACK_SIGNING_SECRET")
    slack_alert_channel: str = Field(default="#hr-alerts", alias="SLACK_ALERT_CHANNEL")

    # ── Google Calendar ───────────────────────────────────────────────────────
    google_application_credentials: str = Field(default="", alias="GOOGLE_APPLICATION_CREDENTIALS")

    # ── Coral ─────────────────────────────────────────────────────────────────
    coral_cache_ttl_seconds: int = Field(default=300, alias="CORAL_CACHE_TTL")
    use_mock_data: bool = Field(default=True, alias="USE_MOCK_DATA")
    mock_data_dir: str = Field(default="mock_data", alias="MOCK_DATA_DIR")

    # ── Agent ─────────────────────────────────────────────────────────────────
    analysis_window_days: int = Field(default=30, alias="ANALYSIS_WINDOW_DAYS")
    high_risk_threshold: float = Field(default=70.0, alias="HIGH_RISK_THRESHOLD")
    medium_risk_threshold: float = Field(default=40.0, alias="MEDIUM_RISK_THRESHOLD")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "populate_by_name": True,
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    """Cached singleton settings — loaded once, reused everywhere."""
    return Settings()
