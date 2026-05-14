from app.clients.mock_client import MockTranslationClient
from app.models.translation_job import TranslationJob
from app.queue.job_store import InMemoryJobStore
from app.queue.translation_queue import InMemoryTranslationQueue
from app.schemas.translation import TranslationStatus
from app.workers.translation_worker import TranslationWorker


def test_worker_processes_queued_job_successfully():
    job_store = InMemoryJobStore()
    translation_queue = InMemoryTranslationQueue()

    job = TranslationJob(
        job_id="job_test_1",
        text="Merhaba",
        source_lang="tr",
        target_lang="en",
    )

    job_store.create_job(job)
    translation_queue.enqueue(job.job_id)

    worker = TranslationWorker(
        job_store=job_store,
        translation_queue=translation_queue,
        translation_client=MockTranslationClient(),
    )

    processed = worker.process_next_job()

    updated_job = job_store.get_job(job.job_id)

    assert processed is True
    assert updated_job is not None
    assert updated_job.status == TranslationStatus.completed
    assert updated_job.translated_text == "[mock-<2en>] Merhaba"
    assert updated_job.error is None


def test_worker_returns_false_when_queue_is_empty():
    job_store = InMemoryJobStore()
    translation_queue = InMemoryTranslationQueue()

    worker = TranslationWorker(
        job_store=job_store,
        translation_queue=translation_queue,
        translation_client=MockTranslationClient(),
    )

    processed = worker.process_next_job()

    assert processed is False


def test_worker_returns_false_when_job_does_not_exist():
    job_store = InMemoryJobStore()
    translation_queue = InMemoryTranslationQueue()

    translation_queue.enqueue("job_missing")

    worker = TranslationWorker(
        job_store=job_store,
        translation_queue=translation_queue,
        translation_client=MockTranslationClient(),
    )

    processed = worker.process_next_job()

    assert processed is False