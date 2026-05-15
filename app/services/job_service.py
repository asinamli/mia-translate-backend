"""
Bu dosyanın görevi:

Job oluşturma, Redis’e kaydetme, queue’ya ekleme ve job status sorgulamayı yönetmek
"""

from app.core.exceptions import AppException
from app.models.translation_job import TranslationJob
from app.queue.job_store import job_store
from app.queue.translation_queue import translation_queue
from app.schemas.job import JobStatusResponse
from app.utils.id_generator import generate_job_id


class JobNotFoundError(AppException):
    def __init__(self, job_id: str):
        super().__init__(
            code="JOB_NOT_FOUND",
            message=f"Job not found: {job_id}",
        )


class JobService:
    def create_translation_job(
        self,
        text: str,
        source_lang: str | None,
        target_lang: str,
    ) -> JobStatusResponse:
        job_id = generate_job_id()

        job = TranslationJob(
            job_id=job_id,
            text=text,
            source_lang=source_lang,
            target_lang=target_lang,
        )

        created_job = job_store.create_job(job)
        translation_queue.enqueue(job_id)

        return self._to_status_response(created_job)

    def get_job_status(self, job_id: str) -> JobStatusResponse:
        job = job_store.get_job(job_id)

        if job is None:
            raise JobNotFoundError(job_id)

        return self._to_status_response(job)

    def _to_status_response(self, job: TranslationJob) -> JobStatusResponse:
        return JobStatusResponse(
            job_id=job.job_id,
            status=job.status,
            source_lang=job.source_lang,
            target_lang=job.target_lang,
            translated_text=job.translated_text,
            error=job.error,
            retry_count=job.retry_count,
        )