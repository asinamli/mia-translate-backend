"""
Bu dosyanın görevi:

Job oluşturma ve job sorgulama iş mantığını yönetmek
"""

from app.core.exceptions import AppException
from app.queue.job_store import job_store
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
        source_lang: str | None,
        target_lang: str,
    ) -> JobStatusResponse:
        job_id = generate_job_id()

        return job_store.create_job(
            job_id=job_id,
            source_lang=source_lang,
            target_lang=target_lang,
        )

    def get_job_status(self, job_id: str) -> JobStatusResponse:
        job = job_store.get_job(job_id)

        if job is None:
            raise JobNotFoundError(job_id)

        return job