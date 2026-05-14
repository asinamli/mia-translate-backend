"""
BU DOSYANIN GÖREVİ
/api/v1/translate endpoint’ini dış dünyaya açmak.
"""

from fastapi import APIRouter, HTTPException, status

from app.core.exceptions import AppException
from app.schemas.translation import TranslationRequest, TranslationResponse
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