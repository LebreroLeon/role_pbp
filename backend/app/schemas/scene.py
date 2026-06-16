from typing import Literal

from pydantic import BaseModel, Field

MessageType = Literal["SPEAK", "ACTION", "CONTEXT", "MASTER", "NARRATIVE", "DICE_ROLL"]
PlayerMessageType = Literal["SPEAK", "ACTION", "CONTEXT"]
SceneStatusType = Literal["ACTIVE", "PAUSED"]


class MemorySettings(BaseModel):
    max_chat_buffer_size: int = 20
    rag_top_k_matches: int = 3


class ChatMessage(BaseModel):
    id: str | None = None
    timestamp: str
    sender_id: str
    type: str
    text: str | None = None
    dice_expression: str | None = None
    raw_result: int | None = None
    final_result: int | None = None
    skill_checked: str | None = None
    read_by: list[str] = Field(default_factory=list)


class SceneState(BaseModel):
    campaign_id: str
    status: str = "ACTIVE"
    location_id: str | None = None
    active_npc_ids: list[str] = Field(default_factory=list)
    scene_objective: str | None = None
    current_turn_player_id: str | None = None
    turn_order: list[str] = Field(default_factory=list)
    memory_settings: MemorySettings = Field(default_factory=MemorySettings)
    chat_buffer: list[ChatMessage] = Field(default_factory=list)
    state_flags: dict = Field(default_factory=dict)


class SceneCreate(BaseModel):
    campaign_id: str
    scene_objective: str | None = None
    turn_order: list[str] = Field(default_factory=list)


class SceneResponse(BaseModel):
    id: str
    campaign_id: str
    status: str
    scene_state: SceneState

    model_config = {"from_attributes": True}


class PostMessageRequest(BaseModel):
    type: str = "ACTION"
    text: str = Field(min_length=1)


class DiceRollRequest(BaseModel):
    dice_expression: str
    modifier: int = 0
    skill_checked: str | None = None


class MarkReadRequest(BaseModel):
    message_ids: list[str] | None = None


class SceneStatusUpdate(BaseModel):
    status: SceneStatusType
