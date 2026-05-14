from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class TranslationMode(str, Enum):
    sync = "sync"
    async_ = "async"


class TranslationStatus(str, Enum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class TranslationItem(BaseModel):
    text: str = Field(..., description="Text to translate")
    source_lang: Optional[str] = Field(default=None, description="Optional source language code")
    target_lang: str = Field(..., description="Required target language code")

    @field_validator("text")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Text cannot be empty.")

        return value

    @field_validator("source_lang", "target_lang")
    @classmethod
    def normalize_language_code(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value

        value = value.strip().lower()

        if not value:
            raise ValueError("Language code cannot be empty.")

        return value


class TranslationRequest(TranslationItem):
    mode: TranslationMode = TranslationMode.sync


class TranslationResponse(BaseModel):
    request_id: str
    mode: TranslationMode
    status: TranslationStatus
    source_lang: Optional[str] = None
    target_lang: str
    translated_text: Optional[str] = None
    job_id: Optional[str] = None


class BatchTranslationRequest(BaseModel):
    items: list[TranslationItem] = Field(..., min_length=1)
    mode: TranslationMode = TranslationMode.async_


class BatchTranslationResponse(BaseModel):
    request_id: str
    mode: TranslationMode
    status: TranslationStatus
    job_ids: list[str] = Field(default_factory=list)