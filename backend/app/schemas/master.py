from pydantic import BaseModel, Field


class MasterAssistRequest(BaseModel):
    campaign_id: str
    scene_id: str
    query: str = Field(min_length=3, max_length=2000)
    focus_entity_id: str | None = None


class MasterAssistResponse(BaseModel):
    query: str
    context_summary: str
    suggestions: list[str]
    note: str | None = None
