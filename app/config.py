"""Application configuration loaded from .env."""
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Tavily
    tavily_api_key: str = ""

    # Server
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    # Rate limiting
    rate_limit_per_minute: int = 20

    # Cache
    cache_ttl_seconds: int = 3600
    redis_url: Optional[str] = None

    # Search
    max_search_pages: int = 3
    tavily_timeout_seconds: float = 15.0


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
