from fastapi import APIRouter, Depends

from app.api.v1.endpoints.jobs import router as jobs_router
from app.api.v1.endpoints.translate import router as translate_router
from app.core.security import verify_bearer_token

api_router = APIRouter(
    dependencies=[Depends(verify_bearer_token)],
)
api_router.include_router(translate_router)
api_router.include_router(jobs_router)