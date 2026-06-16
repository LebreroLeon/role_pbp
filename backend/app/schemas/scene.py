from pydantic import BaseModel, Field


class MemorySettings(BaseModel):
    max_chat_buffer_size: int = 20
    rag_top_k_matches: int = 3


class ChatMessage(BaseModel):
    timestamp: str
    sender_id: str
    type: str
    text: str | None = None
    dice_expression: str | None = None
    raw_result: int | None = None
    final_result: int | None = None
    skill_checked: str | None = None


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
    sender_id: str
    type: str = "NARRATIVE"
    text: str


class DiceRollRequest(BaseModel):
    sender_id: str
    dice_expression: str
    modifier: int = 0
    skill_checked: str | None = None
