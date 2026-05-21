from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_api_allows_request_when_auth_is_disabled(monkeypatch):
    monkeypatch.setenv("API_AUTH_ENABLED", "false")

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


def test_api_rejects_request_without_token_when_auth_is_enabled(monkeypatch):
    monkeypatch.setenv("API_AUTH_ENABLED", "true")
    monkeypatch.setenv("API_BEARER_TOKEN", "test-secret")

    response = client.post(
        "/api/v1/translate",
        json={
            "text": "Merhaba",
            "source_lang": "tr",
            "target_lang": "en",
            "mode": "sync",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "UNAUTHORIZED"


def test_api_accepts_request_with_valid_token_when_auth_is_enabled(monkeypatch):
    monkeypatch.setenv("API_AUTH_ENABLED", "true")
    monkeypatch.setenv("API_BEARER_TOKEN", "test-secret")

    response = client.post(
        "/api/v1/translate",
        headers={
            "Authorization": "Bearer test-secret",
        },
        json={
            "text": "Merhaba",
            "source_lang": "tr",
            "target_lang": "en",
            "mode": "sync",
        },
    )

    assert response.status_code == 200