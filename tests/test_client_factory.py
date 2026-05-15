import pytest

from app.clients.factory import create_translation_client
from app.clients.mock_client import MockTranslationClient
from app.core.config import get_settings
from app.core.exceptions import TranslationClientConfigurationError


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_client_factory_returns_mock_client_by_default(monkeypatch):
    monkeypatch.setenv("TRANSLATION_CLIENT", "mock")

    client = create_translation_client()

    assert isinstance(client, MockTranslationClient)


def test_client_factory_rejects_unknown_client(monkeypatch):
    monkeypatch.setenv("TRANSLATION_CLIENT", "unknown")

    with pytest.raises(TranslationClientConfigurationError):
        create_translation_client()


def test_client_factory_rejects_missing_ctranslate2_model_path(monkeypatch):
    monkeypatch.setenv("TRANSLATION_CLIENT", "ctranslate2")
    monkeypatch.setenv("CTRANSLATE2_MODEL_PATH", "./not-existing-model-path")

    with pytest.raises(TranslationClientConfigurationError):
        create_translation_client()


def test_client_factory_rejects_missing_vertex_config(monkeypatch):
    monkeypatch.setenv("TRANSLATION_CLIENT", "vertex")
    monkeypatch.setenv("VERTEX_PROJECT_ID", "")
    monkeypatch.setenv("VERTEX_LOCATION", "")
    monkeypatch.setenv("VERTEX_ENDPOINT_ID", "")

    with pytest.raises(TranslationClientConfigurationError):
        create_translation_client()