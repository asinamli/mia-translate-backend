from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_sync_translate_returns_mock_translation():
    response = client.post(
        "/api/v1/translate",
        json={
            "text": "Merhaba",
            "source_lang": "tr",
            "target_lang": "en",
            "mode": "sync",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["request_id"].startswith("req_")
    assert data["mode"] == "sync"
    assert data["status"] == "completed"
    assert data["source_lang"] == "tr"
    assert data["target_lang"] == "en"
    assert data["translated_text"] == "[mock-<2en>] Merhaba"


def test_sync_translate_rejects_unsupported_language():
    response = client.post(
        "/api/v1/translate",
        json={
            "text": "Merhaba",
            "source_lang": "tr",
            "target_lang": "xx",
            "mode": "sync",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "UNSUPPORTED_LANGUAGE"


def test_sync_batch_translate_returns_mock_translations():
    response = client.post(
        "/api/v1/translate/batch",
        json={
            "items": [
                {
                    "text": "Merhaba",
                    "source_lang": "tr",
                    "target_lang": "en",
                },
                {
                    "text": "Nasılsın?",
                    "source_lang": "tr",
                    "target_lang": "en",
                },
            ],
            "mode": "sync",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["request_id"].startswith("req_")
    assert data["mode"] == "sync"
    assert data["status"] == "completed"
    assert len(data["items"]) == 2

    assert data["items"][0]["item_index"] == 0
    assert data["items"][0]["translated_text"] == "[mock-<2en>] Merhaba"

    assert data["items"][1]["item_index"] == 1
    assert data["items"][1]["translated_text"] == "[mock-<2en>] Nasılsın?"


def test_batch_translate_rejects_async_mode_until_queue_is_added():
    response = client.post(
        "/api/v1/translate/batch",
        json={
            "items": [
                {
                    "text": "Merhaba",
                    "source_lang": "tr",
                    "target_lang": "en",
                }
            ],
            "mode": "async",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "UNSUPPORTED_TRANSLATION_MODE"