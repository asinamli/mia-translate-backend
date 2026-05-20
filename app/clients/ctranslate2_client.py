# CTranslate2 tabanlı gerçek model inference client.
# Local smoke test için hazır MADLAD CT2 int8 artifact kullanılmaktadır.
# Production için önerilen yol, resmi google/madlad400-3b-mt modelinden
# kontrollü CTranslate2 artifact üretip bu client üzerinden kullanmaktır.

from pathlib import Path
from typing import Any

from app.clients.base import TranslationClient, TranslationInput, TranslationOutput
from app.core.config import get_settings
from app.core.exceptions import (
    TranslationClientConfigurationError,
    TranslationClientRuntimeError,
)

class CTranslate2TranslationClient(TranslationClient):
    def __init__(self):
        settings = get_settings()

        self.model_path = Path(settings.ctranslate2_model_path)
        self.device = settings.ctranslate2_device
        self.compute_type = settings.ctranslate2_compute_type

        self._translator: Any = None
        self._tokenizer: Any = None

        if not self.model_path.exists():
            raise TranslationClientConfigurationError(
                f"CTranslate2 model yolu bulunamadı: {self.model_path}. "
                "Önce CTranslate2 model artifact'i models/ klasörüne indirilmelidir."
            )

        tokenizer_path = self.model_path / "spiece.model"

        if not tokenizer_path.exists():
            raise TranslationClientConfigurationError(
                f"SentencePiece tokenizer bulunamadı: {tokenizer_path}"
            )

    def translate(self, translation_input: TranslationInput) -> TranslationOutput:
        outputs = self.translate_batch([translation_input])
        return outputs[0]

    def translate_batch(
        self,
        translation_inputs: list[TranslationInput],
    ) -> list[TranslationOutput]:
        self._load_model_if_needed()

        tokenized_inputs = []

        for item in translation_inputs:
            input_text = f"{item.target_tag} {item.text}"
            input_tokens = self._tokenizer.encode(input_text, out_type=str)
            tokenized_inputs.append(input_tokens)

        try:
            results = self._translator.translate_batch(
                tokenized_inputs,
                beam_size=1,
                max_decoding_length=128,
                repetition_penalty=2,
                no_repeat_ngram_size=1,
            )
        except Exception as exc:
            raise TranslationClientRuntimeError(
                f"CTranslate2 inference sırasında hata oluştu: {exc}"
            ) from exc

        outputs = []

        for result in results:
            output_tokens = result.hypotheses[0]
            translated_text = self._tokenizer.decode(output_tokens).strip()

            outputs.append(
                TranslationOutput(
                    translated_text=translated_text,
                )
            )

        return outputs

    def _load_model_if_needed(self) -> None:
        if self._translator is not None and self._tokenizer is not None:
            return

        try:
            import ctranslate2
            from sentencepiece import SentencePieceProcessor
        except ImportError as exc:
            raise TranslationClientConfigurationError(
                "CTranslate2 client seçildi ancak gerekli ML bağımlılıkları kurulu değil. "
                "Kurmak için: pip install -r requirements-ml.txt"
            ) from exc

        tokenizer_path = self.model_path / "spiece.model"

        tokenizer = SentencePieceProcessor()
        tokenizer.load(str(tokenizer_path))

        translator = ctranslate2.Translator(
            str(self.model_path),
            device=self.device,
            compute_type=self.compute_type,
        )

        self._tokenizer = tokenizer
        self._translator = translator