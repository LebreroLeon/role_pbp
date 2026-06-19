from datetime import datetime

from pydantic import BaseModel, Field


class OocMessageResponse(BaseModel):
    id: str
    campaign_id: str
    author_user_id: str
    author_display_name: str
    content: str
    message_type: str
    target_user_id: str | None = None
    target_display_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class OocPublicMessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class OocWhisperMessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    target_user_id: str = Field(min_length=1)
