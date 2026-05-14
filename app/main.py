from fastapi import FastAPI

from app.api.v1.endpoints.health import router as health_router
from app.api.v1.router import api_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="FastAPI backend service for Mektup Mia-Translate model integration.",
    version="0.1.0",
)

app.include_router(health_router)
app.include_router(api_router, prefix=settings.api_prefix)