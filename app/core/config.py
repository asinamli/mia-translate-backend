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
    max_input_characters: int = 2000
    max_batch_items: int = 32
    translation_timeout_seconds: int = 30
    max_retries: int = 3

    api_auth_enabled: bool = False
    api_bearer_token: str = "dev-secret"

    cors_allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
    ]

    vertex_project_id: str = ""
    vertex_location: str = ""
    vertex_endpoint_id: str = ""

    triton_url: str = "http://localhost:8001"
    triton_model_name: str = "mia_translate"
    triton_timeout_seconds: int = 30

    ctranslate2_model_path: str = "./models/mia-translate-ct2"
    ctranslate2_device: str = "cpu"
    ctranslate2_compute_type: str = "int8"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",

    
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()