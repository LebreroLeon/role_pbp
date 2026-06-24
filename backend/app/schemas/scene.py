from typing import Literal

from pydantic import BaseModel, Field

MessageType = Literal["SPEAK", "ACTION", "CONTEXT", "MASTER", "NARRATIVE", "DICE_ROLL"]
MessageVisibility = Literal["all", "master_only"]
PlayerMessageType = Literal["SPEAK", "ACTION", "CONTEXT"]
SceneStatusType = Literal["PREPARED", "ACTIVE", "PAUSED", "CLOSED"]
PlayerVisibility = Literal["hidden", "unknown", "visible"]
PreparedSceneStatus = Literal["PREPARED", "ACTIVE"]
SpeakerType = Literal["MASTER", "NPC", "PC", "NARRATOR"]
TurnOrderSource = Literal["initiative", "attribute", "manual"]


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
    rolls: list[int] | None = None
    raw_result: int | None = None
    final_result: int | None = None
    skill_checked: str | None = None
    entity_id: str | None = None
    entity_name: str | None = None
    roll_type: str | None = None
    roll_details: dict | None = None
    chat_summary: str | None = None
    success: bool | None = None
    combat_event: dict | None = None
    read_by: list[str] = Field(default_factory=list)
    like_count: int = 0
    liked_by_user_ids: list[str] = Field(default_factory=list)
    speaker_entity_id: str | None = None
    speaker_display_name: str | None = None
    speaker_type: SpeakerType | None = None
    visibility: MessageVisibility = "all"


class SceneMetadata(BaseModel):
    campaign_id: str
    status: SceneStatusType = "ACTIVE"
    closure_summary: str | None = None


class PreparedEntityRef(BaseModel):
    entity_id: str
    player_visibility: PlayerVisibility = "visible"
    add_to_roster: bool = True


class SceneContext(BaseModel):
    location_id: str | None = None
    active_npc_ids: list[str] = Field(default_factory=list)
    hidden_npc_ids: list[str] = Field(default_factory=list)
    scene_objective: str | None = None
    master_prep_notes: str | None = None
    master_scene_scratchpad: str | None = None
    opening_narration: str | None = None
    prepared_entity_refs: list[PreparedEntityRef] = Field(default_factory=list)


class TurnManagement(BaseModel):
    current_turn_player_id: str | None = None
    turn_order: list[str] = Field(default_factory=list)
    pbp_enabled: bool = False
    order_source: TurnOrderSource = "manual"


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
    hp_current: int | None = None
    hp_max: int | None = None


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
    location_id: str | None = None
    opening_narration: str | None = None
    master_prep_notes: str | None = None
    prepared_entity_refs: list[PreparedEntityRef] = Field(default_factory=list)
    turn_order: list[str] = Field(default_factory=list)
    status: PreparedSceneStatus = "ACTIVE"


class SceneUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=200)


class ScenePrepUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=200)
    scene_objective: str | None = None
    location_id: str | None = None
    opening_narration: str | None = None
    master_prep_notes: str | None = None
    prepared_entity_refs: list[PreparedEntityRef] | None = None


class SceneScratchpadUpdate(BaseModel):
    master_scene_scratchpad: str | None = None


class ActivateSceneRequest(BaseModel):
    send_opening_to_chat: bool = False


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
    advantage: bool = False
    disadvantage: bool = False
    master_only: bool = False


class MarkReadRequest(BaseModel):
    message_ids: list[str] | None = None


class SceneStatusUpdate(BaseModel):
    status: SceneStatusType


class CombatAttackRequest(BaseModel):
    attacker_ref: str = Field(min_length=1)
    defender_ref: str = Field(min_length=1)
    weapon_name: str | None = None
    attack_index: int | None = Field(default=None, ge=0)
    advantage: bool = False
    disadvantage: bool = False


class CombatInitiativeRequest(BaseModel):
    activate_combat: bool = True
    entity_ids: list[str] | None = None


class SceneTurnManagementUpdate(BaseModel):
    pbp_enabled: bool | None = None
    order_source: TurnOrderSource | None = None
    turn_order: list[str] | None = None
    initiative_order: list[InitiativeEntry] | None = None
    current_turn_player_id: str | None = None
    current_turn_entity_id: str | None = None
    resort: bool = False


class LoreAssistRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)


class LoreAssistResponse(BaseModel):
    query: str
    answer: str
    remaining_tokens: int
    generated_at: str
    note: str | None = None


class NpcPresenceEntry(BaseModel):
    entity_id: str
    is_hidden_from_players: bool = False


class ScenePresenceUpdate(BaseModel):
    add: list[NpcPresenceEntry] = Field(default_factory=list)
    remove: list[str] = Field(default_factory=list)


class SceneAddPlayerRequest(BaseModel):
    entity_id: str | None = None
    user_id: str | None = None


class MasterBriefingNpcEntry(BaseModel):
    entity_id: str
    name: str
    voice_and_tone: str | None = None
    secret_lore_master: str | None = None
    player_visibility: PlayerVisibility
    in_roster: bool = False


class MasterBriefingLocation(BaseModel):
    id: str
    name: str


class MasterBriefingResponse(BaseModel):
    scene_id: str
    display_name: str | None = None
    scene_objective: str | None = None
    location: MasterBriefingLocation | None = None
    opening_narration: str | None = None
    master_prep_notes: str | None = None
    last_scene_summary: str | None = None
    arc_manifest: dict | None = None
    npcs: list[MasterBriefingNpcEntry] = Field(default_factory=list)
    prepared_entity_refs: list[PreparedEntityRef] = Field(default_factory=list)


class ScenePickerItem(BaseModel):
    id: str
    scene_number: int
    display_name: str | None = None
    scene_objective: str | None = None
    status: str


class CloseSceneResponse(BaseModel):
    closed_scene: SceneResponse
    prepared_scenes: list[ScenePickerItem] = Field(default_factory=list)
