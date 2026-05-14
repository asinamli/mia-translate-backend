import pytest
from pydantic import ValidationError

from app.core.exceptions import (
    BatchSizeExceededError,
    InputTooLongError,
    UnsupportedLanguageError,
)
from app.schemas.translation import BatchTranslationRequest, TranslationRequest
from app.services.language_service import get_language_tag, is_supported_language
from app.services.validation_service import (
    validate_batch_translation_request,
    validate_translation_request,
)


def test_language_tag_for_supported_language():
    assert get_language_tag("en") == "<2en>"
    assert get_language_tag("tr") == "<2tr>"


def test_supported_language_check():
    assert is_supported_language("tr") is True
    assert is_supported_language("en") is True
    assert is_supported_language("xx") is False


def test_unsupported_language_raises_error():
    with pytest.raises(UnsupportedLanguageError):
        get_language_tag("xx")


def test_translation_request_strips_text_and_language_codes():
    request = TranslationRequest(
        text="  Merhaba  ",
        source_lang=" TR ",
        target_lang=" EN ",
        mode="sync",
    )

    assert request.text == "Merhaba"
    assert request.source_lang == "tr"
    assert request.target_lang == "en"


def test_empty_text_is_rejected_by_schema():
    with pytest.raises(ValidationError):
        TranslationRequest(
            text="   ",
            source_lang="tr",
            target_lang="en",
            mode="sync",
        )


def test_validate_translation_request_accepts_valid_request():
    request = TranslationRequest(
        text="Merhaba",
        source_lang="tr",
        target_lang="en",
        mode="sync",
    )

    validate_translation_request(request)


def test_validate_translation_request_rejects_unsupported_target_language():
    request = TranslationRequest(
        text="Merhaba",
        source_lang="tr",
        target_lang="xx",
        mode="sync",
    )

    with pytest.raises(UnsupportedLanguageError):
        validate_translation_request(request)


def test_validate_translation_request_rejects_long_text():
    request = TranslationRequest(
        text="a" * 3000,
        source_lang="tr",
        target_lang="en",
        mode="sync",
    )

    with pytest.raises(InputTooLongError):
        validate_translation_request(request)


def test_validate_batch_translation_request_accepts_valid_batch():
    request = BatchTranslationRequest(
        items=[
            {
                "text": "Merhaba",
                "source_lang": "tr",
                "target_lang": "en",
            },
            {
                "text": "Nasılsın?",
                "source_lang": "tr",
                "target_lang": "en",
            },
        ],
        mode="async",
    )

    validate_batch_translation_request(request)


def test_validate_batch_translation_request_rejects_too_many_items():
    request = BatchTranslationRequest(
        items=[
            {
                "text": f"Metin {index}",
                "source_lang": "tr",
                "target_lang": "en",
            }
            for index in range(33)
        ],
        mode="async",
    )

    with pytest.raises(BatchSizeExceededError):
        validate_batch_translation_request(request)