from app.clients.mock_client import MockTranslationClient
from app.models.translation_job import TranslationJob
from app.queue.job_store import InMemoryJobStore
from app.queue.translation_queue import InMemoryTranslationQueue
from app.schemas.translation import TranslationStatus
from app.workers.translation_worker import TranslationWorker
from app.clients.base import TranslationClient, TranslationInput, TranslationOutput


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

def test_worker_processes_multiple_jobs_in_one_batch():
    job_store = InMemoryJobStore()
    translation_queue = InMemoryTranslationQueue()

    jobs = [
        TranslationJob(
            job_id="job_batch_1",
            text="Merhaba",
            source_lang="tr",
            target_lang="en",
        ),
        TranslationJob(
            job_id="job_batch_2",
            text="Nasılsın?",
            source_lang="tr",
            target_lang="en",
        ),
        TranslationJob(
            job_id="job_batch_3",
            text="Teşekkürler",
            source_lang="tr",
            target_lang="en",
        ),
    ]

    for job in jobs:
        job_store.create_job(job)
        translation_queue.enqueue(job.job_id)

    worker = TranslationWorker(
        job_store=job_store,
        translation_queue=translation_queue,
        translation_client=MockTranslationClient(),
        max_batch_size=3,
        max_wait_ms=0,
    )

    processed_count = worker.process_next_batch()

    assert processed_count == 3
    assert translation_queue.length() == 0

    first_job = job_store.get_job("job_batch_1")
    second_job = job_store.get_job("job_batch_2")
    third_job = job_store.get_job("job_batch_3")

    assert first_job.status == TranslationStatus.completed
    assert first_job.translated_text == "[mock-<2en>] Merhaba"

    assert second_job.status == TranslationStatus.completed
    assert second_job.translated_text == "[mock-<2en>] Nasılsın?"

    assert third_job.status == TranslationStatus.completed
    assert third_job.translated_text == "[mock-<2en>] Teşekkürler"


def test_worker_respects_max_batch_size():
    job_store = InMemoryJobStore()
    translation_queue = InMemoryTranslationQueue()

    jobs = [
        TranslationJob(
            job_id="job_limit_1",
            text="Birinci",
            source_lang="tr",
            target_lang="en",
        ),
        TranslationJob(
            job_id="job_limit_2",
            text="İkinci",
            source_lang="tr",
            target_lang="en",
        ),
        TranslationJob(
            job_id="job_limit_3",
            text="Üçüncü",
            source_lang="tr",
            target_lang="en",
        ),
    ]

    for job in jobs:
        job_store.create_job(job)
        translation_queue.enqueue(job.job_id)

    worker = TranslationWorker(
        job_store=job_store,
        translation_queue=translation_queue,
        translation_client=MockTranslationClient(),
        max_batch_size=2,
        max_wait_ms=0,
    )

    processed_count = worker.process_next_batch()

    assert processed_count == 2
    assert translation_queue.length() == 1

    first_job = job_store.get_job("job_limit_1")
    second_job = job_store.get_job("job_limit_2")
    third_job = job_store.get_job("job_limit_3")

    assert first_job.status == TranslationStatus.completed
    assert second_job.status == TranslationStatus.completed
    assert third_job.status == TranslationStatus.queued

class FailingTranslationClient(TranslationClient):
    def translate(self, translation_input: TranslationInput) -> TranslationOutput:
        raise RuntimeError("model unavailable")

    def translate_batch(
        self,
        translation_inputs: list[TranslationInput],
    ) -> list[TranslationOutput]:
        raise RuntimeError("model unavailable")


def test_worker_requeues_failed_job_when_retry_limit_is_not_exceeded():
    job_store = InMemoryJobStore()
    translation_queue = InMemoryTranslationQueue()

    job = TranslationJob(
        job_id="job_retry_1",
        text="Merhaba",
        source_lang="tr",
        target_lang="en",
        retry_count=0,
    )

    job_store.create_job(job)
    translation_queue.enqueue(job.job_id)

    worker = TranslationWorker(
        job_store=job_store,
        translation_queue=translation_queue,
        translation_client=FailingTranslationClient(),
        max_batch_size=1,
        max_wait_ms=0,
        max_retries=2,
    )

    processed_count = worker.process_next_batch()

    updated_job = job_store.get_job(job.job_id)

    assert processed_count == 0
    assert updated_job is not None
    assert updated_job.status == TranslationStatus.queued
    assert updated_job.retry_count == 1
    assert updated_job.error == "model unavailable"
    assert translation_queue.length() == 1


def test_worker_marks_job_failed_when_retry_limit_is_reached():
    job_store = InMemoryJobStore()
    translation_queue = InMemoryTranslationQueue()

    job = TranslationJob(
        job_id="job_retry_2",
        text="Merhaba",
        source_lang="tr",
        target_lang="en",
        retry_count=2,
    )

    job_store.create_job(job)
    translation_queue.enqueue(job.job_id)

    worker = TranslationWorker(
        job_store=job_store,
        translation_queue=translation_queue,
        translation_client=FailingTranslationClient(),
        max_batch_size=1,
        max_wait_ms=0,
        max_retries=2,
    )

    processed_count = worker.process_next_batch()

    updated_job = job_store.get_job(job.job_id)

    assert processed_count == 0
    assert updated_job is not None
    assert updated_job.status == TranslationStatus.failed
    assert updated_job.retry_count == 2
    assert updated_job.error == "model unavailable"
    assert translation_queue.length() == 0