from fastapi import APIRouter

from app.api.v1.endpoints.jobs import router as jobs_router
from app.api.v1.endpoints.translate import router as translate_router

api_router = APIRouter()
api_router.include_router(translate_router)
api_router.include_router(jobs_router)