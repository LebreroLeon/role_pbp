from pydantic import BaseModel, EmailStr, Field


class CampaignCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    tone: str | None = None


class CampaignResponse(BaseModel):
    id: str
    name: str
    tone: str | None
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
