from app.core.config import get_settings
from app.core.exceptions import (
    BatchSizeExceededError,
    InputTooLongError,
    UnsupportedLanguageError,
)
from app.schemas.translation import BatchTranslationRequest, TranslationRequest
from app.services.language_service import is_supported_language


def validate_translation_request(request: TranslationRequest) -> None:
    settings = get_settings()

    if request.source_lang and not is_supported_language(request.source_lang):
        raise UnsupportedLanguageError(request.source_lang)

    if not is_supported_language(request.target_lang):
        raise UnsupportedLanguageError(request.target_lang)

    if len(request.text) > settings.max_input_characters:
        raise InputTooLongError(settings.max_input_characters)


def validate_batch_translation_request(request: BatchTranslationRequest) -> None:
    settings = get_settings()

    if len(request.items) > settings.max_batch_items:
        raise BatchSizeExceededError(settings.max_batch_items)

    for item in request.items:
        if item.source_lang and not is_supported_language(item.source_lang):
            raise UnsupportedLanguageError(item.source_lang)

        if not is_supported_language(item.target_lang):
            raise UnsupportedLanguageError(item.target_lang)

        if len(item.text) > settings.max_input_characters:
            raise InputTooLongError(settings.max_input_characters)