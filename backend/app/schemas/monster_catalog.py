from typing import Literal

from pydantic import BaseModel, Field


class MonsterCatalogSummary(BaseModel):
    slug: str
    name: str
    challenge_rating: float
    creature_type: str
    size: str
    source_document: str
    source_label: str = ""


class MonsterCatalogDetail(MonsterCatalogSummary):
    narrative_template: dict
    sheet_template: dict


class MonsterSpawnRequest(BaseModel):
    slug: str
    count: int = Field(default=1, ge=1, le=50)
    player_visibility: Literal["hidden", "unknown", "visible"] | None = None
    hidden: bool = True
    attitude: str = "hostile"


class MonsterSpawnResponse(BaseModel):
    created: list[str]
    count: int
