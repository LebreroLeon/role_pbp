from typing import Literal

from pydantic import BaseModel, Field

MessageType = Literal["SPEAK", "ACTION", "CONTEXT", "MASTER", "NARRATIVE", "DICE_ROLL"]
PlayerMessageType = Literal["SPEAK", "ACTION", "CONTEXT"]
SceneStatusType = Literal["ACTIVE", "PAUSED", "CLOSED"]
SpeakerType = Literal["MASTER", "NPC", "PC", "NARRATOR"]


class MemorySettings(BaseModel):
    max_chat_buffer_size: int = 20
    rag_top_k_matches: int = 3
    max_player_lore_queries_per_scene: int = 3


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
    entity_id: str | None = None
    roll_type: str | None = None
    roll_details: dict | None = None
    combat_event: dict | None = None
    read_by: list[str] = Field(default_factory=list)
    speaker_entity_id: str | None = None
    speaker_display_name: str | None = None
    speaker_type: SpeakerType | None = None


class SceneMetadata(BaseModel):
    campaign_id: str
    status: SceneStatusType = "ACTIVE"
    closure_summary: str | None = None


class SceneContext(BaseModel):
    location_id: str | None = None
    active_npc_ids: list[str] = Field(default_factory=list)
    hidden_npc_ids: list[str] = Field(default_factory=list)
    scene_objective: str | None = None


class TurnManagement(BaseModel):
    current_turn_player_id: str | None = None
    turn_order: list[str] = Field(default_factory=list)


class StateFlags(BaseModel):
    conflict_mode_active: bool = False
    ai_alert_triggered: bool = False
    remaining_player_lore_tokens: int = 3


class InitiativeEntry(BaseModel):
    entity_id: str
    entity_type: str | None = None
    display_name: str | None = None
    initiative_score: int | None = None
    is_active: bool = True


class CombatState(BaseModel):
    is_active: bool = False
    round: int = 0
    initiative_order: list[InitiativeEntry] = Field(default_factory=list)
    current_turn_entity_id: str | None = None
    conflict_mode_active: bool = False


class SceneState(BaseModel):
    metadata: SceneMetadata
    context: SceneContext = Field(default_factory=SceneContext)
    turn_management: TurnManagement = Field(default_factory=TurnManagement)
    memory_settings: MemorySettings = Field(default_factory=MemorySettings)
    chat_buffer: list[ChatMessage] = Field(default_factory=list)
    state_flags: StateFlags = Field(default_factory=StateFlags)
    combat: CombatState = Field(default_factory=CombatState)


class SceneCreate(BaseModel):
    campaign_id: str
    display_name: str | None = Field(default=None, max_length=200)
    scene_objective: str | None = None
    turn_order: list[str] = Field(default_factory=list)


class SceneUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=200)


class SceneResponse(BaseModel):
    id: str
    campaign_id: str
    scene_number: int
    display_name: str | None = None
    status: str
    summary: str | None = None
    scene_state: SceneState

    model_config = {"from_attributes": True}


class PostMessageRequest(BaseModel):
    type: str = "ACTION"
    text: str = Field(min_length=1)
    speaker_entity_id: str | None = None
    speaker_display_name: str | None = None
    speaker_type: SpeakerType | None = None


class DiceRollRequest(BaseModel):
    dice_expression: str
    modifier: int = 0
    skill_checked: str | None = None


class MarkReadRequest(BaseModel):
    message_ids: list[str] | None = None


class SceneStatusUpdate(BaseModel):
    status: SceneStatusType


class CombatAttackRequest(BaseModel):
    attacker_ref: str = Field(min_length=1)
    defender_ref: str = Field(min_length=1)
    weapon_name: str | None = None
    attack_index: int | None = Field(default=None, ge=0)


class CombatInitiativeRequest(BaseModel):
    pass


class NpcPresenceEntry(BaseModel):
    entity_id: str
    is_hidden_from_players: bool = False


class ScenePresenceUpdate(BaseModel):
    add: list[NpcPresenceEntry] = Field(default_factory=list)
    remove: list[str] = Field(default_factory=list)
