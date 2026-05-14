from fastapi import APIRouter, HTTPException, status

from app.core.exceptions import AppException
from app.schemas.translation import (
    BatchTranslationRequest,
    BatchTranslationResponse,
    TranslationRequest,
    TranslationResponse,
)
from app.services.translation_service import TranslationService

router = APIRouter(prefix="/translate", tags=["Translation"])


@router.post("", response_model=TranslationResponse)
def translate(request: TranslationRequest):
    translation_service = TranslationService()

    try:
        return translation_service.translate(request)
    except AppException as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": exc.code,
                "message": exc.message,
            },
        ) from exc


@router.post("/batch", response_model=BatchTranslationResponse)
def translate_batch(request: BatchTranslationRequest):
    translation_service = TranslationService()

    try:
        return translation_service.translate_batch(request)
    except AppException as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": exc.code,
                "message": exc.message,
            },
        ) from exc