# Triton endpointe bağlanmaya hazır client iskeleti olacak

from app.clients.base import TranslationClient, TranslationInput, TranslationOutput
from app.core.config import get_settings
from app.core.exceptions import TranslationClientRuntimeError


class TritonTranslationClient(TranslationClient):
    def __init__(self):
        settings = get_settings()
        self.triton_url = settings.triton_url
        self.model_name = settings.triton_model_name
        self.timeout_seconds = settings.triton_timeout_seconds

    def translate(self, translation_input: TranslationInput) -> TranslationOutput:
        outputs = self.translate_batch([translation_input])
        return outputs[0]

    def translate_batch(
        self,
        translation_inputs: list[TranslationInput],
    ) -> list[TranslationOutput]:
        raise TranslationClientRuntimeError(
            "TritonTranslationClient seçildi ancak Triton model inference payload yapısı "
            "henüz uygulanmadı. Backend Triton entegrasyonuna hazır olacak şekilde "
            "tasarlandı; ancak Triton model repository yapısı ve input/output şeması "
            "netleştirildikten sonra gerçek inference çağrısı eklenecek."
        )