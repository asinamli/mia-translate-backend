"""
Bu dosyanın görevi:

/api/v1 altındaki endpointleri tek yerde toplamak.
"""

from fastapi import APIRouter

from app.api.v1.endpoints.translate import router as translate_router

api_router = APIRouter()
api_router.include_router(translate_router)