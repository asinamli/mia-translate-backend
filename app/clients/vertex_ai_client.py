from app.clients.base import TranslationClient, TranslationInput, TranslationOutput
from app.core.config import get_settings
from app.core.exceptions import TranslationClientConfigurationError


class VertexAITranslationClient(TranslationClient):
    def __init__(self):
        settings = get_settings()

        self.project_id = settings.vertex_project_id
        self.location = settings.vertex_location
        self.endpoint_id = settings.vertex_endpoint_id

        if not self.project_id or not self.location or not self.endpoint_id:
            raise TranslationClientConfigurationError(
                "Vertex AI client seçildi ancak VERTEX_PROJECT_ID, "
                "VERTEX_LOCATION veya VERTEX_ENDPOINT_ID değerlerinden biri eksik."
            )

    def translate(self, translation_input: TranslationInput) -> TranslationOutput:
        outputs = self.translate_batch([translation_input])
        return outputs[0]

    def translate_batch(
        self,
        translation_inputs: list[TranslationInput],
    ) -> list[TranslationOutput]:
        raise TranslationClientConfigurationError(
            "VertexAITranslationClient hazırlandı; ancak gerçek Vertex AI prediction "
            "çağrısı, project, location, endpoint ve credential bilgileri sağlandıktan "
            "sonra aktif edilecektir."
        )