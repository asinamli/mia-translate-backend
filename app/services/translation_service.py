from app.clients.base import TranslationClient, TranslationInput
from app.clients.mock_client import MockTranslationClient
from app.core.exceptions import UnsupportedTranslationModeError
from app.schemas.translation import (
    BatchTranslationItemResponse,
    BatchTranslationRequest,
    BatchTranslationResponse,
    TranslationMode,
    TranslationRequest,
    TranslationResponse,
    TranslationStatus,
)
from app.services.language_service import get_language_tag
from app.services.validation_service import (
    validate_batch_translation_request,
    validate_translation_request,
)
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

    def translate_batch(self, request: BatchTranslationRequest) -> BatchTranslationResponse:
        validate_batch_translation_request(request)

        if request.mode != TranslationMode.sync:
            raise UnsupportedTranslationModeError(request.mode.value)

        request_id = generate_request_id()

        translation_inputs = [
            TranslationInput(
                text=item.text,
                source_lang=item.source_lang,
                target_lang=item.target_lang,
                target_tag=get_language_tag(item.target_lang),
            )
            for item in request.items
        ]

        translation_outputs = self.translation_client.translate_batch(translation_inputs)

        response_items = [
            BatchTranslationItemResponse(
                item_index=index,
                status=TranslationStatus.completed,
                source_lang=request.items[index].source_lang,
                target_lang=request.items[index].target_lang,
                translated_text=translation_outputs[index].translated_text,
            )
            for index in range(len(request.items))
        ]

        return BatchTranslationResponse(
            request_id=request_id,
            mode=request.mode,
            status=TranslationStatus.completed,
            items=response_items,
        )