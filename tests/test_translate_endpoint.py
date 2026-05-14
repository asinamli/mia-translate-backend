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