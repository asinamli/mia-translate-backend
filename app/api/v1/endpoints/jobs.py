"""
Bu dosyanın görevi:

Job durumunu sorgulayan endpoint’i açmak.
"""

from fastapi import APIRouter, HTTPException, status

from app.core.exceptions import AppException
from app.schemas.job import JobStatusResponse
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str):
    job_service = JobService()

    try:
        return job_service.get_job_status(job_id)
    except AppException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": exc.code,
                "message": exc.message,
            },
        ) from exc