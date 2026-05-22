# Triton runtime taslağı - reference implementation
import json
import os
from pathlib import Path
from typing import Any

import numpy as np
#pip install tritonclient[all]
import triton_python_backend_utils as pb_utils


class TritonPythonModel:
    def initialize(self, args: dict[str, Any]) -> None:
        self.model_config = json.loads(args["model_config"])

        self.model_path = Path(self._get_config_value("MODEL_PATH", "/models/madlad400-3b-mt-ct2-int8"))
        self.device = self._get_config_value("DEVICE", "cpu")
        self.compute_type = self._get_config_value("COMPUTE_TYPE", "int8")
        self.max_decoding_length = int(self._get_config_value("MAX_DECODING_LENGTH", "128"))
        self.beam_size = int(self._get_config_value("BEAM_SIZE", "1"))

        if not self.model_path.exists():
            raise RuntimeError(f"CTranslate2 model path not found: {self.model_path}")

        tokenizer_path = self.model_path / "spiece.model"

        if not tokenizer_path.exists():
            raise RuntimeError(f"SentencePiece tokenizer not found: {tokenizer_path}")

        try:
            import ctranslate2
            from sentencepiece import SentencePieceProcessor
        except ImportError as exc:
            raise RuntimeError(
                "Missing Triton runtime dependencies. "
                "ctranslate2 and sentencepiece must be installed in the Triton Python backend environment."
            ) from exc

        tokenizer = SentencePieceProcessor()
        tokenizer.load(str(tokenizer_path))

        translator = ctranslate2.Translator(
            str(self.model_path),
            device=self.device,
            compute_type=self.compute_type,
        )

        self.tokenizer = tokenizer
        self.translator = translator

    def execute(self, requests):
        responses = []

        for request in requests:
            try:
                text_values = self._read_string_input(request, "TEXT")
                source_lang_values = self._read_string_input(request, "SOURCE_LANG")
                target_lang_values = self._read_string_input(request, "TARGET_LANG")
                target_tag_values = self._read_string_input(request, "TARGET_TAG")

                translated_texts = self._translate_batch(
                    text_values=text_values,
                    source_lang_values=source_lang_values,
                    target_lang_values=target_lang_values,
                    target_tag_values=target_tag_values,
                )

                output_array = np.array(
                    [[text] for text in translated_texts],
                    dtype=object,
                )

                output_tensor = pb_utils.Tensor(
                    "TRANSLATED_TEXT",
                    output_array,
                )

                responses.append(
                    pb_utils.InferenceResponse(
                        output_tensors=[output_tensor],
                    )
                )

            except Exception as exc:
                responses.append(
                    pb_utils.InferenceResponse(
                        error=pb_utils.TritonError(str(exc)),
                    )
                )

        return responses

    def finalize(self) -> None:
        pass

    def _translate_batch(
        self,
        text_values: list[str],
        source_lang_values: list[str],
        target_lang_values: list[str],
        target_tag_values: list[str],
    ) -> list[str]:
        tokenized_inputs = []

        for text, source_lang, target_lang, target_tag in zip(
            text_values,
            source_lang_values,
            target_lang_values,
            target_tag_values,
        ):
            final_target_tag = target_tag.strip()

            if not final_target_tag:
                final_target_tag = f"<2{target_lang.strip()}>"

            input_text = f"{final_target_tag} {text}"
            input_tokens = self.tokenizer.encode(input_text, out_type=str)
            tokenized_inputs.append(input_tokens)

        results = self.translator.translate_batch(
            tokenized_inputs,
            beam_size=self.beam_size,
            max_decoding_length=self.max_decoding_length,
            repetition_penalty=2,
            no_repeat_ngram_size=1,
        )

        translated_texts = []

        for result in results:
            output_tokens = result.hypotheses[0]
            translated_text = self.tokenizer.decode(output_tokens).strip()
            translated_texts.append(translated_text)

        return translated_texts

    def _read_string_input(self, request, name: str) -> list[str]:
        tensor = pb_utils.get_input_tensor_by_name(request, name)

        if tensor is None:
            raise RuntimeError(f"Missing required input tensor: {name}")

        values = tensor.as_numpy().reshape(-1)

        return [self._to_string(value) for value in values]

    def _to_string(self, value: Any) -> str:
        if isinstance(value, bytes):
            return value.decode("utf-8")

        if isinstance(value, np.bytes_):
            return value.tobytes().decode("utf-8")

        if value is None:
            return ""

        return str(value)

    def _get_config_value(self, key: str, default: str) -> str:
        env_value = os.getenv(key)

        if env_value:
            return env_value

        parameters = self.model_config.get("parameters", {})
        parameter = parameters.get(key)

        if parameter:
            return parameter.get("string_value", default)

        return default