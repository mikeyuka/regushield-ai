import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "ReguShield AI"
    API_V1_STR: str = "/api/v1"
    
    # Default to SQLite for local development, override with DATABASE_URL in production
    DATABASE_URL: str = "sqlite:///./regushield.db"
    
    # Redis configuration for Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Reddit API Credentials
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""
    REDDIT_USER_AGENT: str = "ReguShield AI v0.1"

    # Anthropic API Key for Claude 3.5 Sonnet validation
    ANTHROPIC_API_KEY: str = ""

    # Payment Gateway Credentials
    STRIPE_SECRET_KEY: str = ""
    GOCARDLESS_ACCESS_TOKEN: str = ""

    # Webhook URL for notifications
    WEBHOOK_URL: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
