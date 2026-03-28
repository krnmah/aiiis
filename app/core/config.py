from functools import lru_cache
from typing import Any, cast

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str
    app_env: str
    app_host: str
    app_port: int
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: int
    db_connect_timeout_seconds: int = 3
    app_log_level: str = "INFO"
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    database_url: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    # BaseSettings resolves required fields from environment/.env at runtime.
    settings_cls = cast(Any, Settings)
    return settings_cls()


def get_database_url(settings: Settings) -> str:
    if settings.database_url:
        return settings.database_url

    return (
        "postgresql+psycopg://"
        f"{settings.postgres_user}:{settings.postgres_password}"
        f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
    )
