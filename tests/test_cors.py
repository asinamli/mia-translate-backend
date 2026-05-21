from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_cors_allows_configured_origin():
    response = client.options(
        "/api/v1/translate",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"