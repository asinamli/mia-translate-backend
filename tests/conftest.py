import os

import pytest

from app.core.config import get_settings


os.environ["APP_ENV"] = "test"
os.environ["TRANSLATION_CLIENT"] = "mock"

os.environ["API_AUTH_ENABLED"] = "false"
os.environ["API_BEARER_TOKEN"] = "test-secret"
os.environ["CORS_ALLOWED_ORIGINS"] = "http://localhost:3000,http://127.0.0.1:3000"

@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()