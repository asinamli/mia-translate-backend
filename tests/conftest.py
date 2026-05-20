import os

import pytest

from app.core.config import get_settings


os.environ["APP_ENV"] = "test"
os.environ["TRANSLATION_CLIENT"] = "mock"


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()