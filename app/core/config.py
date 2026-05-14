from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "mia-translate-backend"
    app_env: str = "local"
    api_prefix: str = "/api/v1"

    translation_client: str = "mock"

    redis_url: str = "redis://localhost:6379/0"

    max_batch_size: int = 8
    max_wait_ms: int = 200
    translation_timeout_seconds: int = 30
    max_retries: int = 3

    api_auth_enabled: bool = False
    api_bearer_token: str = "dev-secret"

    vertex_project_id: str = ""
    vertex_location: str = ""
    vertex_endpoint_id: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()