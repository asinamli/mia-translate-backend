class AppException(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class UnsupportedLanguageError(AppException):
    def __init__(self, language: str):
        super().__init__(
            code="UNSUPPORTED_LANGUAGE",
            message=f"Unsupported language: {language}",
        )


class InputTooLongError(AppException):
    def __init__(self, max_characters: int):
        super().__init__(
            code="INPUT_TOO_LONG",
            message=f"Input text exceeds maximum allowed length of {max_characters} characters.",
        )


class BatchSizeExceededError(AppException):
    def __init__(self, max_items: int):
        super().__init__(
            code="BATCH_SIZE_EXCEEDED",
            message=f"Batch item count cannot exceed {max_items}.",
        )


class UnsupportedTranslationModeError(AppException):
    def __init__(self, mode: str):
        super().__init__(
            code="UNSUPPORTED_TRANSLATION_MODE",
            message=f"Translation mode is not supported in this flow yet: {mode}",
        )

class TranslationClientConfigurationError(AppException):
    def __init__(self, message: str):
        super().__init__(
            code="TRANSLATION_CLIENT_CONFIGURATION_ERROR",
            message=message,
        )


class TranslationClientRuntimeError(AppException):
    def __init__(self, message: str):
        super().__init__(
            code="TRANSLATION_CLIENT_RUNTIME_ERROR",
            message=message,
        )