from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. All values come from environment variables (see infra/.env.example)."""

    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False, extra="ignore")

    app_name: str = "Threadhall"
    # Runtime role: DML only. Migrations use MIGRATION_DATABASE_URL (owner role) via alembic.
    database_url: str = "postgresql+psycopg://app_runtime:app_runtime_dev@localhost:5432/threadhall"
    db_pool_size: int = 10
    db_max_overflow: int = 10

    access_token_ttl_seconds: int = 15 * 60
    refresh_token_ttl_seconds: int = 30 * 24 * 3600

    # Only trust X-Forwarded-For when running behind a reverse proxy you control.
    trust_proxy_headers: bool = False

    # In-process rate limits (single-process deployment; put edge limits in the reverse proxy too).
    auth_rate_limit_per_minute: int = 20
    write_rate_limit_per_minute: int = 60
    community_create_per_hour: int = 5

    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
