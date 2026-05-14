"""
Bu dosyanın görevi:

Çeviri job_id’lerini Redis listesine eklemek. Worker daha sonra bu listeden job_id alacak.
"""

from app.queue.redis_client import get_redis_client


class InMemoryTranslationQueue:
    def __init__(self):
        self._queue: list[str] = []

    def enqueue(self, job_id: str) -> None:
        self._queue.append(job_id)

    def dequeue(self) -> str | None:
        if not self._queue:
            return None

        return self._queue.pop(0)

    def length(self) -> int:
        return len(self._queue)


class RedisTranslationQueue:
    def __init__(self, queue_key: str = "translation_jobs:queue"):
        self.queue_key = queue_key

    def enqueue(self, job_id: str) -> None:
        redis_client = get_redis_client()
        redis_client.rpush(self.queue_key, job_id)

    def dequeue(self) -> str | None:
        redis_client = get_redis_client()
        return redis_client.lpop(self.queue_key)

    def length(self) -> int:
        redis_client = get_redis_client()
        return redis_client.llen(self.queue_key)


translation_queue = RedisTranslationQueue()

"""
Burada rpush şunu yapıyor
job_id değerini Redis listesinin sonuna ekliyor
Worker daha sonra lpop veya blpop ile sıradan iş alacak
"""