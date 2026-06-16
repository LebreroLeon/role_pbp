from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class EntityType(StrEnum):
    NPC = "NPC"
    PC = "PC"
    FACTION = "FACTION"
    LOCATION = "LOCATION"
    RELATIONSHIP = "RELATIONSHIP"
    ARC_MANIFEST = "ARC_MANIFEST"


# --- Shared blocks ---


class SystemMechanics(BaseModel):
    system_name: str
    power_scale: str
    stats_summary: dict[str, str] = Field(default_factory=dict)
    notable_features: list[str] = Field(default_factory=list)


class PCSystemMechanics(BaseModel):
    system_name: str
    stats_summary: dict[str, str] = Field(default_factory=dict)
    notable_features: list[str] = Field(default_factory=list)


# --- NPC ---


class NPCMetadata(BaseModel):
    type: Literal["NPC"] = "NPC"
    system_agnostic: Literal[True]
    version: str


class NPCIdentity(BaseModel):
    name: str
    concept: str
    faction_id: str
    current_location_id: str


class AINarrativeProfile(BaseModel):
    public_description: str
    secret_lore_master: str
    personality_traits: list[str]
    voice_and_tone: str


class NPCStateFlags(BaseModel):
    is_dead: bool
    is_present_in_scene: bool
    attitude_towards_party: str
    has_met_party: bool


class EntityNPCDocument(BaseModel):
    metadata: NPCMetadata
    identity: NPCIdentity
    ai_narrative_profile: AINarrativeProfile
    system_mechanics: SystemMechanics
    state_flags: NPCStateFlags


# --- PC ---


class PCMetadata(BaseModel):
    type: Literal["PC"]
    system_agnostic: Literal[True]
    version: str


class PCIdentity(BaseModel):
    name: str
    concept: str
    faction_id: str | None = None
    current_location_id: str


class PlayerBinding(BaseModel):
    user_id: str
    is_active_in_campaign: bool


class PublicProfile(BaseModel):
    description: str
    personality_traits: list[str] = Field(default_factory=list)


class PCStateFlags(BaseModel):
    is_present_in_scene: bool
    is_incapacitated: bool


class EntityPCDocument(BaseModel):
    metadata: PCMetadata
    identity: PCIdentity
    player_binding: PlayerBinding
    public_profile: PublicProfile | None = None
    system_mechanics: PCSystemMechanics
    state_flags: PCStateFlags


# --- Faction ---


class FactionMetadata(BaseModel):
    type: Literal["FACTION"]
    version: str


class FactionIdentity(BaseModel):
    name: str
    faction_type: str
    headquarters_location_id: str | None = None


class FactionNarrativeProfile(BaseModel):
    public_description: str
    secret_lore_master: str
    goals: list[str] = Field(default_factory=list)


class FactionStateFlags(BaseModel):
    attitude_towards_party: str
    influence_level: int = Field(ge=0, le=10)
    is_active: bool


class EntityFactionDocument(BaseModel):
    metadata: FactionMetadata
    identity: FactionIdentity
    narrative_profile: FactionNarrativeProfile
    state_flags: FactionStateFlags


# --- Location ---


class LocationMetadata(BaseModel):
    type: Literal["LOCATION"]
    version: str


class LocationIdentity(BaseModel):
    name: str
    location_type: str
    parent_location_id: str | None = None


class LocationNarrativeProfile(BaseModel):
    public_description: str
    secret_lore_master: str
    ambient_tone: str | None = None
    notable_features: list[str] = Field(default_factory=list)


class LocationStateFlags(BaseModel):
    is_accessible_to_party: bool
    danger_level: int = Field(ge=0, le=10)
    is_destroyed: bool = False


class EntityLocationDocument(BaseModel):
    metadata: LocationMetadata
    identity: LocationIdentity
    narrative_profile: LocationNarrativeProfile
    state_flags: LocationStateFlags


# --- Relationship ---


class RelationshipMetadata(BaseModel):
    type: Literal["RELATIONSHIP"]
    created_at: datetime
    last_updated: datetime


class RelationshipConnection(BaseModel):
    source_id: str
    target_id: str
    is_bidirectional: bool


class NarrativeBond(BaseModel):
    bond_type: str
    public_status: str
    secret_nuance: str
    tension_level: int = Field(ge=0, le=10)


class AIBehaviorGuidelines(BaseModel):
    if_source_acts: str
    if_target_acts: str


class RelationshipStateFlags(BaseModel):
    is_secret_discovered_by_party: bool
    is_active: bool


class EntityRelationshipDocument(BaseModel):
    metadata: RelationshipMetadata
    connection: RelationshipConnection
    narrative_bond: NarrativeBond
    ai_behavior_guidelines: AIBehaviorGuidelines
    state_flags: RelationshipStateFlags


# --- Arc Manifest ---


class ArcMetadata(BaseModel):
    type: Literal["ARC_MANIFEST"]


class PlotLine(BaseModel):
    title: str
    global_summary: str
    current_act: int = Field(ge=1)
    narrative_tone: str


class ActiveQuest(BaseModel):
    quest_id: str
    title: str
    description: str
    required_triggers: list[str] = Field(default_factory=list)
    secret_dm_notes: str


class CompletedMilestone(BaseModel):
    milestone_id: str
    description: str
    resolved_at: datetime


class ArcStateFlags(BaseModel):
    is_main_plot_derailed: bool
    world_threat_level: int = Field(ge=0, le=10)


class EntityArcManifestDocument(BaseModel):
    metadata: ArcMetadata
    plot_line: PlotLine
    active_quests: list[ActiveQuest] = Field(default_factory=list)
    completed_milestones: list[CompletedMilestone] = Field(default_factory=list)
    state_flags: ArcStateFlags


ENTITY_DOCUMENT_MODELS: dict[EntityType, type[BaseModel]] = {
    EntityType.NPC: EntityNPCDocument,
    EntityType.PC: EntityPCDocument,
    EntityType.FACTION: EntityFactionDocument,
    EntityType.LOCATION: EntityLocationDocument,
    EntityType.RELATIONSHIP: EntityRelationshipDocument,
    EntityType.ARC_MANIFEST: EntityArcManifestDocument,
}


class EntityCreate(BaseModel):
    campaign_id: str
    entity_type: EntityType
    document: dict


class EntityUpdate(BaseModel):
    document: dict


class EntityResponse(BaseModel):
    id: str
    campaign_id: str
    entity_type: EntityType
    document: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
