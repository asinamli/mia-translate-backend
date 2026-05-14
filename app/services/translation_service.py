from app.clients.base import TranslationClient, TranslationInput
from app.clients.mock_client import MockTranslationClient
from app.schemas.translation import (
    TranslationRequest,
    TranslationResponse,
    TranslationStatus,
)
from app.services.language_service import get_language_tag
from app.services.validation_service import validate_translation_request
from app.utils.id_generator import generate_request_id


class TranslationService:
    def __init__(self, translation_client: TranslationClient | None = None):
        self.translation_client = translation_client or MockTranslationClient()

    def translate(self, request: TranslationRequest) -> TranslationResponse:
        validate_translation_request(request)

        request_id = generate_request_id()
        target_tag = get_language_tag(request.target_lang)

        translation_input = TranslationInput(
            text=request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            target_tag=target_tag,
        )

        translation_output = self.translation_client.translate(translation_input)

        return TranslationResponse(
            request_id=request_id,
            mode=request.mode,
            status=TranslationStatus.completed,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            translated_text=translation_output.translated_text,
        )