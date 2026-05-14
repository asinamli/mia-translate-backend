"""
Bu dosyanın görevi:

Job bilgilerini geçici olarak saklamak.
"""
# Şu an bunu local çalışan bir store olarak yazıyoruz
# Sonraki adımda Redis karşılığı gelecek

from app.schemas.job import JobStatusResponse
from app.schemas.translation import TranslationStatus


class InMemoryJobStore:
    def __init__(self):
        self._jobs: dict[str, JobStatusResponse] = {}

    def create_job(
        self,
        job_id: str,
        source_lang: str | None,
        target_lang: str,
    ) -> JobStatusResponse:
        job = JobStatusResponse(
            job_id=job_id,
            status=TranslationStatus.queued,
            source_lang=source_lang,
            target_lang=target_lang,
        )

        self._jobs[job_id] = job
        return job

    def get_job(self, job_id: str) -> JobStatusResponse | None:
        return self._jobs.get(job_id)

    def update_job(
        self,
        job_id: str,
        status: TranslationStatus,
        translated_text: str | None = None,
        error: str | None = None,
    ) -> JobStatusResponse | None:
        job = self._jobs.get(job_id)

        if job is None:
            return None

        updated_job = JobStatusResponse(
            job_id=job.job_id,
            status=status,
            source_lang=job.source_lang,
            target_lang=job.target_lang,
            translated_text=translated_text,
            error=error,
        )

        self._jobs[job_id] = updated_job
        return updated_job


job_store = InMemoryJobStore()