from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class DocumentType(StrEnum):
    RULES = "RULES"
    ADVENTURE = "ADVENTURE"
    NOTES = "NOTES"
    EXPORT = "EXPORT"
    OTHER = "OTHER"


class DocumentResponse(BaseModel):
    id: str
    campaign_id: str
    filename: str
    original_name: str
    document_type: DocumentType
    mime_type: str | None
    size_bytes: int
    created_at: datetime

    model_config = {"from_attributes": True}
