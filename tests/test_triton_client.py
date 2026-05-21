import pytest

from app.clients.base import TranslationInput
from app.clients.triton_client import TritonTranslationClient
from app.core.config import get_settings
from app.core.exceptions import TranslationClientRuntimeError


def set_triton_env(monkeypatch):
    monkeypatch.setenv("TRITON_URL", "http://localhost:8001")
    monkeypatch.setenv("TRITON_MODEL_NAME", "mia_translate")
    monkeypatch.setenv("TRITON_TIMEOUT_SECONDS", "30")
    get_settings.cache_clear()


def test_triton_client_normalizes_url(monkeypatch):
    set_triton_env(monkeypatch)

    client = TritonTranslationClient()

    assert client.url == "localhost:8001"


def test_triton_client_translates_with_contract(monkeypatch):
    set_triton_env(monkeypatch)

    client = TritonTranslationClient()
    captured = {}

    def fake_predict(instances):
        captured["instances"] = instances
        return ["Hello"]

    monkeypatch.setattr(client, "_predict", fake_predict)

    output = client.translate(
        TranslationInput(
            text="Merhaba",
            source_lang="tr",
            target_lang="en",
            target_tag="<2en>",
        )
    )

    assert output.translated_text == "Hello"
    assert captured["instances"] == [
        {
            "text": "Merhaba",
            "source_lang": "tr",
            "target_lang": "en",
            "target_tag": "<2en>",
        }
    ]


def test_triton_client_raises_when_prediction_count_mismatch(monkeypatch):
    set_triton_env(monkeypatch)

    client = TritonTranslationClient()

    monkeypatch.setattr(client, "_predict", lambda instances: [])

    with pytest.raises(TranslationClientRuntimeError):
        client.translate(
            TranslationInput(
                text="Merhaba",
                source_lang="tr",
                target_lang="en",
                target_tag="<2en>",
            )
        )