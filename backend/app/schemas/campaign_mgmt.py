from pydantic import BaseModel, EmailStr, Field


class CampaignCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    tone: str | None = None
    game_system: str | None = Field(default=None, max_length=64)


class CampaignResponse(BaseModel):
    id: str
    name: str
    tone: str | None
    game_system: str | None = None
    role: str

    model_config = {"from_attributes": True}


class CampaignMemberAdd(BaseModel):
    email: EmailStr
    role: str = Field(default="PLAYER", pattern="^(MASTER|PLAYER)$")


class CampaignMemberResponse(BaseModel):
    user_id: str
    email: str
    display_name: str
    role: str
