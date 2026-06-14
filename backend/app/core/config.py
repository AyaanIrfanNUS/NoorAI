"""
Application configuration.

This file reads settings from the .env file and makes them available
throughout the app as a single, typed object called `settings`.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str

    # SECRET_KEY signs and verifies all JWTs (access + refresh tokens).
    # If this value changes:
    #   - Every existing access token becomes invalid immediately
    #     (signature no longer verifies), forcing all logged-in users
    #     to log in again.
    #   - Refresh tokens stored in Redis also become unusable, since
    #     decode_token() can no longer verify them - effectively the
    #     same as revoking every active session.
    SECRET_KEY: str
    GROQ_API_KEY: str = ""
    TAVILY_API_KEY: str = ""

    APP_ENV: str = "development"
    FRONTEND_URL: str = ""
    SENTRY_DSN: str = ""

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()