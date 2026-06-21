from pydantic import BaseModel, Field


class UnreadCountsResponse(BaseModel):
    play: int = Field(ge=0, description="Unread in-character scene chat (Jugar)")
    ooc: int = Field(ge=0, description="Unread out-of-character messages")
