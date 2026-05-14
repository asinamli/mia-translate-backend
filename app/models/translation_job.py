"""
Bu dosyanın görevi:

Redis’te saklayacağımız job kaydının iç modelini tanımlamak.
"""

from typing import Optional

from pydantic import BaseModel

from app.schemas.translation import TranslationStatus


class TranslationJob(BaseModel):
    job_id: str
    text: str
    source_lang: Optional[str] = None
    target_lang: str
    status: TranslationStatus = TranslationStatus.queued
    translated_text: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0
    # Buradaki text alanı API response’ta dönmeyecek ama worker daha sonra bu metni Redisten okuyup çevirecek