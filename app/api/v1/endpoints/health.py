from fastapi import APIRouter

from app.core.config import get_settings
from app.queue.redis_client import check_redis_connection

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    settings = get_settings()

    return {
        "status": "ok",
        "service": settings.app_name,
    }


@router.get("/ready")
def readiness_check():
    settings = get_settings()

    redis_connected = check_redis_connection()

    return {
        "status": "ready" if redis_connected else "not_ready",
        "service": settings.app_name,
        "environment": settings.app_env,
        "checks": {
            "config": "ok",
            "translation_client": settings.translation_client,
            "redis": "ok" if redis_connected else "failed",
            "redis_url_configured": bool(settings.redis_url),
            "vertex_configured": bool(
                settings.vertex_project_id
                and settings.vertex_location
                and settings.vertex_endpoint_id
            ),
        },
    }