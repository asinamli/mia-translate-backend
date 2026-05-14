import pytest
from fastapi.testclient import TestClient

import app.services.job_service as job_service_module
from app.main import app
from app.queue.job_store import InMemoryJobStore
from app.queue.translation_queue import InMemoryTranslationQueue

client = TestClient(app)


@pytest.fixture(autouse=True)
def use_in_memory_job_dependencies(monkeypatch):
    monkeypatch.setattr(job_service_module, "job_store", InMemoryJobStore())
    monkeypatch.setattr(job_service_module, "translation_queue", InMemoryTranslationQueue())


def test_async_translate_creates_queued_job():
    response = client.post(
        "/api/v1/translate",
        json={
            "text": "Merhaba",
            "source_lang": "tr",
            "target_lang": "en",
            "mode": "async",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["request_id"].startswith("req_")
    assert data["job_id"].startswith("job_")
    assert data["mode"] == "async"
    assert data["status"] == "queued"
    assert data["translated_text"] is None


def test_get_created_job_status_returns_queued():
    create_response = client.post(
        "/api/v1/translate",
        json={
            "text": "Merhaba",
            "source_lang": "tr",
            "target_lang": "en",
            "mode": "async",
        },
    )

    job_id = create_response.json()["job_id"]

    status_response = client.get(f"/api/v1/jobs/{job_id}")

    assert status_response.status_code == 200

    data = status_response.json()

    assert data["job_id"] == job_id
    assert data["status"] == "queued"
    assert data["source_lang"] == "tr"
    assert data["target_lang"] == "en"


def test_get_unknown_job_returns_404():
    response = client.get("/api/v1/jobs/job_unknown")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "JOB_NOT_FOUND"


def test_async_translate_enqueues_job():
    response = client.post(
        "/api/v1/translate",
        json={
            "text": "Merhaba",
            "source_lang": "tr",
            "target_lang": "en",
            "mode": "async",
        },
    )

    assert response.status_code == 200
    assert response.json()["job_id"].startswith("job_")