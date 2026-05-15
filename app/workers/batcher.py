import time
from app.core.config import get_settings

class JobBatcher:
    def __init__(
        self,
        translation_queue,
        max_batch_size: int | None = None,
        max_wait_ms: int | None = None,
    ):
        settings = get_settings()

        self.translation_queue = translation_queue
        self.max_batch_size = max_batch_size or settings.max_batch_size
        self.max_wait_ms = settings.max_wait_ms if max_wait_ms is None else max_wait_ms


    def collect_job_ids(self) -> list[str]:
        first_job_id = self.translation_queue.dequeue()

        if first_job_id is None:
            return []
        
        job_ids = [first_job_id]
        deadline = time.monotonic() + (self.max_wait_ms / 1000)

        while len(job_ids) < self.max_batch_size:
            next_job_id = self.translation_queue.dequeue()

            if next_job_id is not None:
                job_ids.append(next_job_id)
                continue

            if time.monotonic() >= deadline:
                break

            time.sleep(0.01)

        return job_ids
