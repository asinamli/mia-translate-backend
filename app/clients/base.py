from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TranslationInput:
    text: str
    target_lang: str
    target_tag: str
    source_lang: Optional[str] = None


@dataclass(frozen=True)
class TranslationOutput:
    translated_text: str


class TranslationClient(ABC):
    @abstractmethod
    def translate(self, translation_input: TranslationInput) -> TranslationOutput:
        pass

    @abstractmethod
    def translate_batch(
        self,
        translation_inputs: list[TranslationInput],
    ) -> list[TranslationOutput]:
        pass