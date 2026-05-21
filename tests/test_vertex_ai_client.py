import pytest

from app.clients.base import TranslationInput
from app.clients.vertex_ai_client import VertexAITranslationClient
from app.core.config import get_settings
from app.core.exceptions import TranslationClientConfigurationError


class FakeVertexResponse:
    def __init__(self, predictions):
        self.predictions = predictions


class FakeVertexEndpoint:
    def __init__(self, predictions):
        self.predictions = predictions
        self.instances = None

    def predict(self, instances):
        self.instances = instances
        return FakeVertexResponse(self.predictions)


def set_vertex_env(monkeypatch):
    monkeypatch.setenv("VERTEX_PROJECT_ID", "test-project")
    monkeypatch.setenv("VERTEX_LOCATION", "us-central1")
    monkeypatch.setenv("VERTEX_ENDPOINT_ID", "123456789")
    get_settings.cache_clear()


def test_vertex_client_requires_endpoint_config(monkeypatch):
    monkeypatch.setenv("VERTEX_PROJECT_ID", "")
    monkeypatch.setenv("VERTEX_LOCATION", "")
    monkeypatch.setenv("VERTEX_ENDPOINT_ID", "")
    get_settings.cache_clear()

    with pytest.raises(TranslationClientConfigurationError):
        VertexAITranslationClient()


def test_vertex_client_translates_dict_prediction(monkeypatch):
    set_vertex_env(monkeypatch)

    client = VertexAITranslationClient()
    fake_endpoint = FakeVertexEndpoint(
        predictions=[
            {
                "translated_text": "Hello"
            }
        ]
    )

    monkeypatch.setattr(client, "_load_endpoint_if_needed", lambda: fake_endpoint)

    output = client.translate(
        TranslationInput(
            text="Merhaba",
            source_lang="tr",
            target_lang="en",
            target_tag="<2en>",
        )
    )

    assert output.translated_text == "Hello"
    assert fake_endpoint.instances == [
        {
            "text": "Merhaba",
            "source_lang": "tr",
            "target_lang": "en",
            "target_tag": "<2en>",
        }
    ]


def test_vertex_client_translates_string_prediction(monkeypatch):
    set_vertex_env(monkeypatch)

    client = VertexAITranslationClient()
    fake_endpoint = FakeVertexEndpoint(predictions=["Hello"])

    monkeypatch.setattr(client, "_load_endpoint_if_needed", lambda: fake_endpoint)

    output = client.translate(
        TranslationInput(
            text="Merhaba",
            source_lang="tr",
            target_lang="en",
            target_tag="<2en>",
        )
    )

    assert output.translated_text == "Hello"