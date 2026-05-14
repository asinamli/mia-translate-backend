"""
Bu dosyanın görevi:

Redis bağlantısını tek merkezden yönetmek ve Redis ayakta mı kontrol etmek
"""

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings


def get_redis_client() -> Redis:
    settings = get_settings()

    return Redis.from_url(
        settings.redis_url,
        decode_responses=True,
    )


def check_redis_connection() -> bool:
    try:
        redis_client = get_redis_client()
        return bool(redis_client.ping())
    except RedisError:
        return False