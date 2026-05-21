from typing import Any

from app.clients.base import TranslationClient, TranslationInput, TranslationOutput
from app.core.config import get_settings
from app.core.exceptions import (
    TranslationClientConfigurationError,
    TranslationClientRuntimeError,
)


class VertexAITranslationClient(TranslationClient):
    def __init__(self):
        settings = get_settings()

        self.project_id = settings.vertex_project_id
        self.location = settings.vertex_location
        self.endpoint_id = settings.vertex_endpoint_id

        if not self.project_id or not self.location or not self.endpoint_id:
            raise TranslationClientConfigurationError(
                "Vertex AI client seçildi ancak VERTEX_PROJECT_ID, "
                "VERTEX_LOCATION veya VERTEX_ENDPOINT_ID eksik."
            )

        self._endpoint: Any = None

    def translate(self, translation_input: TranslationInput) -> TranslationOutput:
        outputs = self.translate_batch([translation_input])
        return outputs[0]

    def translate_batch(
        self,
        translation_inputs: list[TranslationInput],
    ) -> list[TranslationOutput]:
        endpoint = self._load_endpoint_if_needed()

        instances = [
            {
                "text": item.text,
                "source_lang": item.source_lang,
                "target_lang": item.target_lang,
                "target_tag": item.target_tag,
            }
            for item in translation_inputs
        ]

        try:
            response = endpoint.predict(instances=instances)
        except Exception as exc:
            raise TranslationClientRuntimeError(
                f"Vertex AI prediction sırasında hata oluştu: {exc}"
            ) from exc

        predictions = getattr(response, "predictions", None)

        if predictions is None:
            raise TranslationClientRuntimeError(
                "Vertex AI response içinde predictions alanı bulunamadı."
            )

        if len(predictions) != len(translation_inputs):
            raise TranslationClientRuntimeError(
                "Vertex AI response item sayısı request item sayısı ile eşleşmiyor."
            )

        return [
            TranslationOutput(
                translated_text=self._extract_translated_text(prediction),
            )
            for prediction in predictions
        ]

    def _load_endpoint_if_needed(self):
        if self._endpoint is not None:
            return self._endpoint

        try:
            from google.cloud import aiplatform
        except ImportError as exc:
            raise TranslationClientConfigurationError(
                "Vertex AI client seçildi ancak google-cloud-aiplatform kurulu değil. "
                "Kurmak için: pip install -r requirements-cloud.txt"
            ) from exc

        endpoint_name = (
            f"projects/{self.project_id}/locations/{self.location}/"
            f"endpoints/{self.endpoint_id}"
        )

        self._endpoint = aiplatform.Endpoint(endpoint_name=endpoint_name)
        return self._endpoint

    @staticmethod
    def _extract_translated_text(prediction: Any) -> str:
        if isinstance(prediction, str):
            return prediction

        if isinstance(prediction, dict):
            for key in ("translated_text", "translation", "text", "output"):
                value = prediction.get(key)
                if isinstance(value, str):
                    return value

        raise TranslationClientRuntimeError(
            "Vertex AI prediction formatı desteklenmiyor. "
            "Beklenen format: string veya translated_text/translation/text/output alanı içeren dict."
        )