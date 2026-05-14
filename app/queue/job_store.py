"""
Bu dosyanın görevi:

Job kayıtlarını saklamak. Artık ana yapı Redis olacak. Testlerde kullanmak için InMemory yapı da kalacak.
"""
from app.models.translation_job import TranslationJob
from app.queue.redis_client import get_redis_client
from app.schemas.translation import TranslationStatus


class InMemoryJobStore:
    def __init__(self):
        self._jobs: dict[str, TranslationJob] = {}

    def create_job(self, job: TranslationJob) -> TranslationJob:
        self._jobs[job.job_id] = job
        return job

    def get_job(self, job_id: str) -> TranslationJob | None:
        return self._jobs.get(job_id)

    def update_job(
        self,
        job_id: str,
        status: TranslationStatus,
        translated_text: str | None = None,
        error: str | None = None,
    ) -> TranslationJob | None:
        job = self._jobs.get(job_id)

        if job is None:
            return None

        updated_job = job.model_copy(
            update={
                "status": status,
                "translated_text": translated_text,
                "error": error,
            }
        )

        self._jobs[job_id] = updated_job
        return updated_job


class RedisJobStore:
    def __init__(self, key_prefix: str = "translation_job:", ttl_seconds: int = 24 * 60 * 60):
        self.key_prefix = key_prefix
        self.ttl_seconds = ttl_seconds

    def _get_key(self, job_id: str) -> str:
        return f"{self.key_prefix}{job_id}"

    def create_job(self, job: TranslationJob) -> TranslationJob:
        redis_client = get_redis_client()

        redis_client.setex(
            name=self._get_key(job.job_id),
            time=self.ttl_seconds,
            value=job.model_dump_json(),
        )

        return job

    def get_job(self, job_id: str) -> TranslationJob | None:
        redis_client = get_redis_client()
        raw_job = redis_client.get(self._get_key(job_id))

        if raw_job is None:
            return None

        return TranslationJob.model_validate_json(raw_job)

    def update_job(
        self,
        job_id: str,
        status: TranslationStatus,
        translated_text: str | None = None,
        error: str | None = None,
    ) -> TranslationJob | None:
        job = self.get_job(job_id)

        if job is None:
            return None

        updated_job = job.model_copy(
            update={
                "status": status,
                "translated_text": translated_text,
                "error": error,
            }
        )

        redis_client = get_redis_client()

        redis_client.setex(
            name=self._get_key(job_id),
            time=self.ttl_seconds,
            value=updated_job.model_dump_json(),
        )

        return updated_job


job_store = RedisJobStore()
#Şu an uygulama gerçek çalışırken RedisJobStore kullanacak. Testlerde ise bunu monkeypatch ile InMemoryJobStore yapacağız