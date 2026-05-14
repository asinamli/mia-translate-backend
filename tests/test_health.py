from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "mia-translate-backend",
    }


def test_readiness_check_returns_ready_when_redis_is_available(monkeypatch):
    from app.api.v1.endpoints import health

    monkeypatch.setattr(health, "check_redis_connection", lambda: True)

    response = client.get("/ready")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ready"
    assert data["checks"]["config"] == "ok"
    assert data["checks"]["translation_client"] == "mock"
    assert data["checks"]["redis"] == "ok"


def test_readiness_check_returns_not_ready_when_redis_is_unavailable(monkeypatch):
    from app.api.v1.endpoints import health

    monkeypatch.setattr(health, "check_redis_connection", lambda: False)

    response = client.get("/ready")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "not_ready"
    assert data["checks"]["redis"] == "failed"