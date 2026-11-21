"""Centralized application configuration using Pydantic Settings."""

import json
import os
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings loaded from environment variables and defaults."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = Field(
        default="Urban Air Quality Assistant API",
        description="Application title",
    )
    APP_VERSION: str = Field(
        default="1.0.0",
        description="Semantic application version",
    )
    APP_ENV: str = Field(
        default="development",
        description="Runtime environment: development, staging, production, or test",
    )
    API_V1_PREFIX: str = Field(
        default="/api/v1",
        description="Routing prefix for v1 API endpoints",
    )
    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"],
        description="Allowed CORS origins",
    )
    DATABASE_URL: str = Field(
        default="sqlite:///./air_quality.db",
        description="Database connection URL",
    )
    GEMINI_API_KEY: str | None = Field(
        default=None,
        description="Optional Gemini AI API key",
    )
    GEMINI_MODEL: str = Field(
        default="gemini-3.5-flash-lite",
        description="Configured Gemini model identifier",
    )
    AI_PROVIDER: str = Field(
        default="gemini",
        description="Configured AI health provider: 'gemini' or 'mock'",
    )
    AI_ENABLED: bool = Field(
        default=True,
        description="Master switch to enable or disable AI health guidance features",
    )
    AI_REQUEST_TIMEOUT: int = Field(
        default=30,
        description="AI generation timeout in seconds",
    )
    AI_MAX_RETRIES: int = Field(
        default=2,
        description="Maximum retry attempts for transient AI provider failures",
    )
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level",
    )

    # External Provider Configuration (CPCB / data.gov.in)
    CPCB_API_BASE_URL: str = Field(
        default="https://api.data.gov.in/resource/3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69",
        description="Official CPCB real-time AQI dataset endpoint on data.gov.in",
    )
    CPCB_API_KEY: str | None = Field(
        default=None,
        description="Optional API key for data.gov.in platform",
    )
    AQI_PROVIDER: str = Field(
        default="cpcb",
        description="Active AQI provider: 'cpcb' or 'mock'",
    )
    AQI_FETCH_TIMEOUT: float = Field(
        default=10.0,
        description="HTTP request timeout in seconds for provider calls",
    )
    AQI_CACHE_TTL_SECONDS: int = Field(
        default=300,
        description="Cache time-to-live in seconds for external observations",
    )
    AQI_MAX_RETRIES: int = Field(
        default=2,
        description="Maximum retry attempts for transient HTTP failures",
    )
    SYNC_ADMIN_SECRET: str | None = Field(
        default=None,
        description="Optional administrative secret key required for POST /api/v1/air-quality/sync",
    )

    # Alerts and Notifications Configuration
    ALERTS_ENABLED: bool = Field(
        default=True,
        description="Master toggle for background alert detection and notifications",
    )
    ALERT_POLL_INTERVAL_SECONDS: int = Field(
        default=300,
        description="Interval in seconds between background alert processing evaluations",
    )
    ALERT_DETERIORATION_THRESHOLD: int = Field(
        default=30,
        description="Minimum AQI increase required to trigger a sudden deterioration alert",
    )
    ALERT_IMPROVEMENT_THRESHOLD: int = Field(
        default=40,
        description="Minimum AQI decrease required to trigger a significant improvement alert",
    )
    ALERT_EXPIRATION_HOURS: int = Field(
        default=24,
        description="Hours after creation before an alert automatically expires",
    )
    ALERT_ADMIN_SECRET: str | None = Field(
        default=None,
        description="Optional secret key required for POST /api/v1/alerts/process in production",
    )

    # Web Push Notifications (VAPID)
    WEB_PUSH_ENABLED: bool = Field(
        default=False,
        description="Toggle to enable browser web push notifications",
    )
    VAPID_PUBLIC_KEY: str | None = Field(
        default=None,
        description="VAPID application server public key for Web Push",
    )
    VAPID_PRIVATE_KEY: str | None = Field(
        default=None,
        description="VAPID application server private key for Web Push",
    )
    VAPID_SUBJECT: str = Field(
        default="mailto:admin@urbanairquality.org",
        description="Contact subject URI for VAPID push payload",
    )

    # Weather Integration Configuration
    WEATHER_PROVIDER: str = Field(
        default="open-meteo",
        description="Active meteorological data provider: 'open-meteo' or 'mock'",
    )
    WEATHER_API_KEY: str | None = Field(
        default=None,
        description="Optional API key for external weather provider",
    )
    WEATHER_API_BASE_URL: str = Field(
        default="https://api.open-meteo.com/v1",
        description="Base URL for weather provider API calls",
    )
    WEATHER_REQUEST_TIMEOUT: float = Field(
        default=10.0,
        description="Timeout in seconds for external weather API requests",
    )
    WEATHER_ENABLED: bool = Field(
        default=True,
        description="Whether weather integration is enabled for meteorological feature augmentation",
    )
    WEATHER_CACHE_TTL_SECONDS: int = Field(
        default=900,
        description="Cache time-to-live in seconds for weather observations (15 minutes)",
    )

    # Forecasting Engine Configuration
    FORECAST_MODEL: str = Field(
        default="exponential_smoothing",
        description="Active forecasting model family: 'exponential_smoothing', 'moving_average', 'persistence'",
    )
    FORECAST_MIN_TRAINING_SAMPLES: int = Field(
        default=24,
        description="Minimum chronological historical observations required to train or evaluate forecasting model",
    )
    FORECAST_ADMIN_SECRET: str | None = Field(
        default=None,
        description="Optional administrative secret key required for POST /api/v1/forecast/generate",
    )
    FORECAST_DEFAULT_HORIZON_HOURS: int = Field(
        default=24,
        description="Default prediction horizon in hours",
    )
    TRUSTED_PROXY: bool = Field(
        default=False,
        description="When True, trust the X-Forwarded-For header for client IP extraction (use only behind a known proxy)",
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_database_url(cls, v: str | None) -> str:
        """Handle default database URL and serverless environment adjustments."""
        url = v or "sqlite:///./air_quality.db"
        if (os.getenv("VERCEL") == "1" or os.getenv("AWS_LAMBDA_FUNCTION_NAME")) and url.startswith("sqlite:///."):
            return "sqlite:////tmp/air_quality.db"
        return url

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from a JSON array string, comma-separated string, or list."""
        if isinstance(v, str):
            stripped = v.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                try:
                    parsed = json.loads(stripped)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except json.JSONDecodeError:
                    pass
            return [item.strip() for item in stripped.split(",") if item.strip()]
        elif isinstance(v, (list, tuple)):
            return [str(item).strip() for item in v if str(item).strip()]
        return ["http://localhost:5173", "http://127.0.0.1:5173"]

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.APP_ENV.lower() in ("development", "dev", "local", "test")

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.APP_ENV.lower() in ("production", "prod")


@lru_cache
def get_settings() -> Settings:
    """Retrieve cached application settings instance."""
    return Settings()
