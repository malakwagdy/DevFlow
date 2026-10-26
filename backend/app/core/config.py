from functools import lru_cache
from typing import Literal

from cryptography.fernet import Fernet
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str
    # HS256 needs a key of at least 32 bytes (RFC 7518 §3.2).
    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    cors_allowed_origins: list[str] = ["http://localhost:3000"]
    # Where the browser is sent back to after GitHub OAuth.
    frontend_url: str = "http://localhost:3000"

    # GitHub OAuth App. Optional: without them the /github endpoints return 503.
    github_client_id: str | None = None
    github_client_secret: str | None = None
    github_redirect_uri: str = "http://localhost:8000/github/callback"
    github_token_encryption_key: str | None = None

    # Emails (verification, password reset). "console" logs them instead of
    # sending, for local development; "smtp" sends through the server below.
    email_backend: Literal["console", "smtp"] = "console"
    email_from: str = "DevFlow <no-reply@devflow.local>"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    # STARTTLS on port 587 (most providers); set false only for a local test server.
    smtp_starttls: bool = True

    email_verification_expire_hours: int = 24
    password_reset_expire_minutes: int = 30

    # Off only for load tests; the limits themselves live in app/core/rate_limit.py.
    rate_limit_enabled: bool = True

    @field_validator(
        "github_client_id",
        "github_client_secret",
        "github_token_encryption_key",
        "smtp_host",
        "smtp_username",
        "smtp_password",
        mode="before",
    )
    @classmethod
    def empty_to_none(cls, value: object) -> object:
        return value or None

    @field_validator("github_token_encryption_key")
    @classmethod
    def must_be_fernet_key(cls, value: str | None) -> str | None:
        if value is not None:
            Fernet(value.encode())  # raises ValueError for a malformed key
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
