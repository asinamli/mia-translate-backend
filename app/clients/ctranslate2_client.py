# CTranslate2 için iskelet olacak
# bu client ileride Mia-Translate’in CTranslate2 formatına dönüştürülmüş halini kullanacak

from pathlib import Path

from app.clients.base import TranslationClient, TranslationInput, TranslationOutput
from app.core.config import get_settings
from app.core.exceptions import TranslationClientConfigurationError


class CTranslate2TranslationClient(TranslationClient):
    def __init__(self):
        settings = get_settings()

        self.model_path = Path(settings.ctranslate2_model_path)
        self.device = settings.ctranslate2_device
        self.compute_type = settings.ctranslate2_compute_type

        if not self.model_path.exists():
            raise TranslationClientConfigurationError(
                f"CTranslate2 model yolu bulunamadı: {self.model_path}. "
                "Bu client aktif edilmeden önce Mia-Translate modeli CTranslate2 formatına "
                "dönüştürülmelidir."
            )

    def translate(self, translation_input: TranslationInput) -> TranslationOutput:
        outputs = self.translate_batch([translation_input])
        return outputs[0]

    def translate_batch(
        self,
        translation_inputs: list[TranslationInput],
    ) -> list[TranslationOutput]:
        raise TranslationClientConfigurationError(
            "CTranslate2TranslationClient hazırlandı; ancak gerçek CTranslate2 inference "
            "akışı, Mia-Translate modeli CTranslate2 formatına dönüştürüldükten sonra "
            "aktif edilecektir."
        )