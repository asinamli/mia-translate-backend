from app.core.exceptions import UnsupportedLanguageError

SUPPORTED_LANGUAGES = {
    "tr": "Turkish",
    "en": "English",
    "ar": "Arabic",
    "de": "German",
    "fr": "French",
    "ru": "Russian",
    "es": "Spanish",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese",
}


def normalize_language_code(language: str) -> str:
    return language.strip().lower()


def is_supported_language(language: str) -> bool:
    normalized_language = normalize_language_code(language)
    return normalized_language in SUPPORTED_LANGUAGES


def get_language_tag(language: str) -> str:
    normalized_language = normalize_language_code(language)

    if not is_supported_language(normalized_language):
        raise UnsupportedLanguageError(normalized_language)

    return f"<2{normalized_language}>"


def get_supported_languages() -> dict[str, str]:
    return SUPPORTED_LANGUAGES