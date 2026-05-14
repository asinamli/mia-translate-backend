from app.clients.base import TranslationClient, TranslationInput, TranslationOutput


class MockTranslationClient(TranslationClient):
    def translate(self, translation_input: TranslationInput) -> TranslationOutput:
        return TranslationOutput(
            translated_text=f"[mock-{translation_input.target_tag}] {translation_input.text}"
        )

    def translate_batch(
        self,
        translation_inputs: list[TranslationInput],
    ) -> list[TranslationOutput]:
        return [
            self.translate(translation_input)
            for translation_input in translation_inputs
        ]