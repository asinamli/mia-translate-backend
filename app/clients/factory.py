# bu dosya client seçimi yapacak
from app.clients.base import TranslationClient
from app.clients.ctranslate2_client import CTranslate2TranslationClient
from app.clients.mock_client import MockTranslationClient
from app.clients.triton_client import TritonTranslationClient
from app.clients.vertex_ai_client import VertexAITranslationClient
from app.core.config import get_settings
from app.core.exceptions import TranslationClientConfigurationError


def create_translation_client() -> TranslationClient:
    settings = get_settings()
    client_name = settings.translation_client.strip().lower()

    if client_name == "mock":
        return MockTranslationClient()

    if client_name == "triton":
        return TritonTranslationClient()

    if client_name == "ctranslate2":
        return CTranslate2TranslationClient()

    if client_name == "vertex":
        return VertexAITranslationClient()

    raise TranslationClientConfigurationError(
        f"Desteklenmeyen translation client seçildi: {settings.translation_client}. "
        "Desteklenen değerler: mock, triton, ctranslate2, vertex."
    )