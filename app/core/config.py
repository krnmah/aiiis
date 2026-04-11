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
    llm_provider: str = "huggingface"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.2:3b"
    ollama_timeout_seconds: int = 60
    huggingface_api_token: str | None = None
    huggingface_model: str = "google/flan-t5-base"
    huggingface_chat_completions_url: str = "https://router.huggingface.co/v1/chat/completions"
    huggingface_timeout_seconds: int = 60
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    openai_chat_completions_url: str = "https://api.openai.com/v1/chat/completions"
    openai_timeout_seconds: int = 60
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    redis_enabled: bool = True
    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str | None = None
    redis_cache_ttl_seconds: int = 120
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
