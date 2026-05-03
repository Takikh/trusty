"""
Application configuration — loads all settings from the .env file.

Uses pydantic-settings for validated, typed config with sensible defaults.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central settings object. Values are loaded from the .env file at the
    project root. Any value can be overridden by setting the corresponding
    environment variable.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # ignore extra keys in .env that we don't define here
    )

    # ── Supabase ────────────────────────────────────────────────────────
    supabase_url: str
    supabase_key: str
    supabase_service_key: str

    # ── JWT ──────────────────────────────────────────────────────────────
    jwt_secret: str = "change-me-to-a-random-secret"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60

    # ── Email (Gmail SMTP) ──────────────────────────────────────────────
    email_username: str
    email_app_password: str

    # ── Admin seed credentials ──────────────────────────────────────────
    admin_email: str = "admin@clinicverify.local"
    admin_password: str = "admin"


# Singleton — import this throughout the app
settings = Settings()
