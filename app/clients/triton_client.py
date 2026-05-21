from typing import Any
from urllib.parse import urlparse

from app.clients.base import TranslationClient, TranslationInput, TranslationOutput
from app.core.config import get_settings
from app.core.exceptions import (
    TranslationClientConfigurationError,
    TranslationClientRuntimeError,
)


class TritonTranslationClient(TranslationClient):
    def __init__(self):
        settings = get_settings()

        self.url = self._normalize_url(settings.triton_url)
        self.model_name = settings.triton_model_name
        self.timeout_seconds = settings.triton_timeout_seconds

        if not self.url:
            raise TranslationClientConfigurationError(
                "Triton client seçildi ancak TRITON_URL eksik."
            )

        if not self.model_name:
            raise TranslationClientConfigurationError(
                "Triton client seçildi ancak TRITON_MODEL_NAME eksik."
            )

        self._client: Any = None

    def translate(self, translation_input: TranslationInput) -> TranslationOutput:
        outputs = self.translate_batch([translation_input])
        return outputs[0]

    def translate_batch(
        self,
        translation_inputs: list[TranslationInput],
    ) -> list[TranslationOutput]:
        instances = [
            {
                "text": item.text,
                "source_lang": item.source_lang,
                "target_lang": item.target_lang,
                "target_tag": item.target_tag,
            }
            for item in translation_inputs
        ]

        predictions = self._predict(instances)

        if len(predictions) != len(translation_inputs):
            raise TranslationClientRuntimeError(
                "Triton response item sayısı request item sayısı ile eşleşmiyor."
            )

        return [
            TranslationOutput(translated_text=translated_text)
            for translated_text in predictions
        ]

    def _predict(self, instances: list[dict[str, str]]) -> list[str]:
        try:
            import numpy as np
            import tritonclient.http as httpclient
        except ImportError as exc:
            raise TranslationClientConfigurationError(
                "Triton client seçildi ancak gerekli bağımlılıklar kurulu değil. "
                "Kurmak için: pip install -r requirements-triton.txt"
            ) from exc

        client = self._load_client_if_needed()

        text_values = np.array([[item["text"]] for item in instances], dtype=object)
        source_lang_values = np.array(
            [[item["source_lang"]] for item in instances],
            dtype=object,
        )
        target_lang_values = np.array(
            [[item["target_lang"]] for item in instances],
            dtype=object,
        )
        target_tag_values = np.array(
            [[item["target_tag"]] for item in instances],
            dtype=object,
        )

        inputs = []

        for name, values in [
            ("TEXT", text_values),
            ("SOURCE_LANG", source_lang_values),
            ("TARGET_LANG", target_lang_values),
            ("TARGET_TAG", target_tag_values),
        ]:
            infer_input = httpclient.InferInput(name, values.shape, "BYTES")
            infer_input.set_data_from_numpy(values)
            inputs.append(infer_input)

        outputs = [
            httpclient.InferRequestedOutput("TRANSLATED_TEXT"),
        ]

        try:
            response = client.infer(
                model_name=self.model_name,
                inputs=inputs,
                outputs=outputs,
                client_timeout=self.timeout_seconds,
            )
        except Exception as exc:
            raise TranslationClientRuntimeError(
                f"Triton inference sırasında hata oluştu: {exc}"
            ) from exc

        raw_output = response.as_numpy("TRANSLATED_TEXT")

        if raw_output is None:
            raise TranslationClientRuntimeError(
                "Triton response içinde TRANSLATED_TEXT output'u bulunamadı."
            )

        return self._decode_output(raw_output)

    def _load_client_if_needed(self):
        if self._client is not None:
            return self._client

        try:
            import tritonclient.http as httpclient
        except ImportError as exc:
            raise TranslationClientConfigurationError(
                "Triton client seçildi ancak tritonclient kurulu değil. "
                "Kurmak için: pip install -r requirements-triton.txt"
            ) from exc

        self._client = httpclient.InferenceServerClient(url=self.url)
        return self._client

    @staticmethod
    def _normalize_url(url: str) -> str:
        if not url:
            return ""

        parsed = urlparse(url)

        if parsed.scheme:
            return parsed.netloc + parsed.path

        return url

    @staticmethod
    def _decode_output(raw_output: Any) -> list[str]:
        try:
            flat_values = raw_output.reshape(-1)
        except AttributeError:
            flat_values = raw_output

        decoded_values = []

        for value in flat_values:
            if isinstance(value, bytes):
                decoded_values.append(value.decode("utf-8"))
            elif isinstance(value, str):
                decoded_values.append(value)
            elif isinstance(value, list) and value:
                inner = value[0]
                if isinstance(inner, bytes):
                    decoded_values.append(inner.decode("utf-8"))
                else:
                    decoded_values.append(str(inner))
            else:
                decoded_values.append(str(value))

        return decoded_values