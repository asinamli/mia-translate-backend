"""
Bu dosyanın görevi:

Redis queue’dan job almak, çeviri yapmak ve job durumunu Redis’te güncellemek.
"""

import argparse
import time

from app.clients.base import TranslationClient, TranslationInput
from app.clients.mock_client import MockTranslationClient
from app.core.exceptions import AppException
from app.queue.job_store import RedisJobStore
from app.queue.translation_queue import RedisTranslationQueue
from app.schemas.translation import TranslationStatus
from app.services.language_service import get_language_tag


class TranslationWorker:
    def __init__(
        self,
        job_store: RedisJobStore | None = None,
        translation_queue: RedisTranslationQueue | None = None,
        translation_client: TranslationClient | None = None,
    ):
        self.job_store = job_store or RedisJobStore()
        self.translation_queue = translation_queue or RedisTranslationQueue()
        self.translation_client = translation_client or MockTranslationClient()

    def process_next_job(self) -> bool:
        job_id = self.translation_queue.dequeue()

        if job_id is None:
            return False

        job = self.job_store.get_job(job_id)

        if job is None:
            return False

        self.job_store.update_job(
            job_id=job.job_id,
            status=TranslationStatus.processing,
        )

        try:
            target_tag = get_language_tag(job.target_lang)

            translation_input = TranslationInput(
                text=job.text,
                source_lang=job.source_lang,
                target_lang=job.target_lang,
                target_tag=target_tag,
            )

            translation_output = self.translation_client.translate(translation_input)

            self.job_store.update_job(
                job_id=job.job_id,
                status=TranslationStatus.completed,
                translated_text=translation_output.translated_text,
            )

            return True

        except AppException as exc:
            self.job_store.update_job(
                job_id=job.job_id,
                status=TranslationStatus.failed,
                error=exc.message,
            )

            return False

        except Exception as exc:
            self.job_store.update_job(
                job_id=job.job_id,
                status=TranslationStatus.failed,
                error=str(exc),
            )

            return False

    def run_forever(self, poll_interval_seconds: float = 1.0) -> None:
        while True:
            processed = self.process_next_job()

            if not processed:
                time.sleep(poll_interval_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(description="Mia Translate background worker")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process only one queued job and exit.",
    )

    args = parser.parse_args()

    worker = TranslationWorker()

    if args.once:
        processed = worker.process_next_job()
        print({"processed": processed})
        return

    worker.run_forever()


if __name__ == "__main__":
    main()