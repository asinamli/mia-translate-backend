"""
Bu dosyanın görevi:

Async job durumunu API response olarak tanımlamak.
"""

from typing import Optional

from pydantic import BaseModel

from app.schemas.translation import TranslationStatus


class JobStatusResponse(BaseModel):
    job_id: str
    status: TranslationStatus
    source_lang: Optional[str] = None
    target_lang: Optional[str] = None
    translated_text: Optional[str] = None
    error: Optional[str] = None