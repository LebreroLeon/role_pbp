from datetime import datetime

from pydantic import BaseModel, Field


class SystemManualFileStatus(BaseModel):
    filename: str
    path: str
    indexed: bool
    indexed_at: datetime | None = None
    chunk_count: int = 0


class SystemManualStatusResponse(BaseModel):
    system_id: str
    files: list[SystemManualFileStatus] = Field(default_factory=list)
