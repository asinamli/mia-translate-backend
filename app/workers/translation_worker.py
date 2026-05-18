import argparse
import time
from collections import defaultdict

from app.clients.base import TranslationClient, TranslationInput
from app.clients.factory import create_translation_client
from app.core.config import get_settings
from app.core.exceptions import AppException
from app.models.translation_job import TranslationJob
from app.queue.job_store import RedisJobStore
from app.queue.translation_queue import RedisTranslationQueue
from app.schemas.translation import TranslationStatus
from app.services.language_service import get_language_tag
from app.workers.batcher import JobBatcher

from app.core.logging import configure_logging, get_logger

logger = get_logger("app.workers.translation_worker")

class TranslationWorker:
    def __init__(
        self,
        job_store: RedisJobStore | None = None,
        translation_queue: RedisTranslationQueue | None = None,
        translation_client: TranslationClient | None = None,
        max_batch_size: int | None = None,
        max_wait_ms: int | None = None,
        max_retries: int | None = None,
    ):
        settings = get_settings()

        self.job_store = job_store or RedisJobStore()
        self.translation_queue = translation_queue or RedisTranslationQueue()
        self.translation_client = translation_client or create_translation_client()
        self.max_retries = settings.max_retries if max_retries is None else max_retries

        self.batcher = JobBatcher(
            translation_queue=self.translation_queue,
            max_batch_size=max_batch_size,
            max_wait_ms=max_wait_ms,
        )

    def process_next_job(self) -> bool:
        job_id = self.translation_queue.dequeue()

        if job_id is None:
            return False

        processed_count = self._process_job_ids([job_id])
        return processed_count > 0

    def process_next_batch(self) -> int:
        job_ids = self.batcher.collect_job_ids()

        if job_ids:
            logger.info(
                "Worker batch collected",
                extra={
                    "batch_size": len(job_ids),
                },
            )

        return self._process_job_ids(job_ids)

    def _process_job_ids(self, job_ids: list[str]) -> int:
        jobs = []

        for job_id in job_ids:
            job = self.job_store.get_job(job_id)

            if job is None:
                continue

            self.job_store.update_job(
                job_id=job.job_id,
                status=TranslationStatus.processing,
            )

            jobs.append(job)

        if not jobs:
            return 0

        jobs_by_target_lang = defaultdict(list)

        for job in jobs:
            jobs_by_target_lang[job.target_lang].append(job)

        processed_count = 0

        for target_lang, grouped_jobs in jobs_by_target_lang.items():
            try:
                translation_inputs = [
                    TranslationInput(
                        text=job.text,
                        source_lang=job.source_lang,
                        target_lang=job.target_lang,
                        target_tag=get_language_tag(target_lang),
                    )
                    for job in grouped_jobs
                ]

                translation_outputs = self.translation_client.translate_batch(
                    translation_inputs
                )

                for job, translation_output in zip(grouped_jobs, translation_outputs):
                    self.job_store.update_job(
                        job_id=job.job_id,
                        status=TranslationStatus.completed,
                        translated_text=translation_output.translated_text,
                        error=None,
                    )

                    logger.info(
                        "Job completed",
                        extra={
                            "job_id": job.job_id,
                            "status": TranslationStatus.completed.value,
                        },
                    )

                    processed_count += 1

            except AppException as exc:
                for job in grouped_jobs:
                    self._handle_job_failure(job, exc.message)

            except Exception as exc:
                for job in grouped_jobs:
                    self._handle_job_failure(job, str(exc))

        return processed_count

    def _handle_job_failure(self, job: TranslationJob, error_message: str) -> None:
        next_retry_count = job.retry_count + 1

        if job.retry_count < self.max_retries:
            self.job_store.update_job(
                job_id=job.job_id,
                status=TranslationStatus.queued,
                error=error_message,
                retry_count=next_retry_count,
            )

            self.translation_queue.enqueue(job.job_id)

            logger.warning(
                "Job requeued after failure",
                extra={
                    "job_id": job.job_id,
                    "status": TranslationStatus.queued.value,
                    "retry_count": next_retry_count,
                },
            )

            return

        self.job_store.update_job(
            job_id=job.job_id,
            status=TranslationStatus.failed,
            error=error_message,
            retry_count=job.retry_count,
        )
        logger.error(
            "Job failed permanently",
            extra={
                "job_id": job.job_id,
                "status": TranslationStatus.failed.value,
                "retry_count": job.retry_count,
            },
        )

    def run_forever(self, poll_interval_seconds: float = 1.0) -> None:
        while True:
            processed_count = self.process_next_batch()

            if processed_count == 0:
                time.sleep(poll_interval_seconds)


def main() -> None:
    configure_logging()

    parser = argparse.ArgumentParser(description="Mia Translate background worker")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process one batch of queued jobs and exit.",
    )

    args = parser.parse_args()

    worker = TranslationWorker()

    if args.once:
        processed_count = worker.process_next_batch()
        print({"processed": processed_count})
        return

    worker.run_forever()


if __name__ == "__main__":
    main()