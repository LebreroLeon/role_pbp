import type { AuthUser } from "../types/auth";



export type AuthResponse = {

  access_token: string;

  token_type: string;

  user: AuthUser;

};



export type Campaign = {

  id: string;

  name: string;

  tone: string | null;

  game_system: string | null;

  role: "MASTER" | "PLAYER";

};



export type DocumentType = "RULES" | "ADVENTURE" | "NOTES" | "EXPORT" | "OTHER";



export type CampaignDocument = {

  id: string;

  campaign_id: string;

  filename: string;

  original_name: string;

  document_type: DocumentType;

  mime_type: string | null;

  size_bytes: number;

  created_at: string;

};



export type EntityExportBundle = {

  version: string;

  campaign_id: string;

  exported_at: string;

  entities: Array<{ entity_type: EntityType; document: Record<string, unknown> }>;

};



export type CampaignMember = {

  user_id: string;

  email: string;

  display_name: string;

  role: "MASTER" | "PLAYER";

};



export type OocMessageType = "OOC_PUBLIC" | "OOC_WHISPER";



export type OocMessage = {

  id: string;

  campaign_id: string;

  author_user_id: string;

  author_display_name: string;

  content: string;

  message_type: OocMessageType;

  target_user_id: string | null;

  target_display_name: string | null;

  created_at: string;

};



export type MessageType = "SPEAK" | "ACTION" | "CONTEXT" | "MASTER" | "DICE_ROLL" | "NARRATIVE" | "COMBAT";



export type CombatAttackRollSummary = {

  total: number;

  hit?: boolean;

  natural_20?: boolean;

  natural_1?: boolean;

  target_ac?: number;

  modifier?: number;

  expression?: string;

  rolls?: number[];

  chat_summary?: string;

};



export type CombatDamageSummary = {

  amount: number;

  type?: string;

};



export type CombatEventKind =

  | "ATTACK_RESOLVED"

  | "DAMAGE_APPLIED"

  | "INITIATIVE"

  | "COMBAT_START"

  | "COMBAT_END"

  | string;



export type CombatEvent = {

  kind: CombatEventKind;

  attacker_id?: string;

  attacker_name?: string;

  defender_id?: string;

  defender_name?: string;

  attack_roll?: CombatAttackRollSummary;

  damage?: CombatDamageSummary;

  defender_hp_remaining?: number;

  defender_hp_max?: number;

  weapon_name?: string;

  hp?: {

    before?: number;

    after?: number;

  };

};



export type CombatAttackRequest = {

  attacker_ref: string;

  defender_ref: string;

  weapon_name?: string;

  attack_index?: number;

};



export type ChatMessage = {

  id?: string;

  timestamp: string;

  sender_id: string;

  type: MessageType | string;

  text?: string;

  dice_expression?: string;

  raw_result?: number;

  final_result?: number;

  skill_checked?: string | null;

  read_by?: string[];

  like_count?: number;

  liked_by_user_ids?: string[];

  /** Entidad que realizó la tirada (PC/NPC). */

  entity_id?: string;

  entity_name?: string;

  /** Tipo contextual: skill_check, attack_roll, damage, initiative, … */

  roll_type?: string;

  roll_details?: Record<string, unknown>;

  success?: boolean;

  chat_summary?: string;

  /** Payload estructurado para mensajes type COMBAT o DICE_ROLL de combate. */

  combat_event?: CombatEvent;

  /** Identidad narrativa elegida por el Máster (impersonación). */

  speaker_entity_id?: string;

  speaker_display_name?: string;

  speaker_type?: "MASTER" | "NPC" | "PC" | "NARRATOR";

};



export type SceneStatusType = "ACTIVE" | "PAUSED" | "CLOSED";



export type SceneMetadata = {

  campaign_id: string;

  status: SceneStatusType;

  closure_summary?: string | null;

};



export type SceneContext = {

  location_id: string | null;

  active_npc_ids: string[];

  hidden_npc_ids?: string[];

  scene_objective: string | null;

};



export type NpcPresenceEntry = {

  entity_id: string;

  is_hidden_from_players?: boolean;

};



export type ScenePresenceUpdate = {

  add?: NpcPresenceEntry[];

  remove?: string[];

};



export type SceneAddPlayerRequest = {

  entity_id?: string;

  user_id?: string;

};


export type SceneTurnManagementUpdate = {
  pbp_enabled?: boolean;
  order_source?: TurnOrderSource;
  turn_order?: string[];
  initiative_order?: CombatInitiativeEntry[];
  current_turn_player_id?: string | null;
  current_turn_entity_id?: string | null;
  resort?: boolean;
};

export type LoreAssistResponse = {
  query: string;
  answer: string;
  remaining_tokens: number;
  generated_at: string;
  note?: string | null;
};

export type SystemManualFileStatus = {
  filename: string;
  path: string;
  indexed: boolean;
  indexed_at?: string | null;
  chunk_count: number;
};

export type SystemManualStatusResponse = {
  system_id: string;
  files: SystemManualFileStatus[];
};


export type CombatInitiativeRequest = {
  activate_combat?: boolean;
};



export type TurnOrderSource = "initiative" | "attribute" | "manual";



export type TurnManagement = {

  current_turn_player_id: string | null;

  turn_order: string[];

  pbp_enabled: boolean;

  order_source: TurnOrderSource;

};



export type MemorySettings = {

  max_chat_buffer_size: number;

  rag_top_k_matches: number;

  max_player_lore_queries_per_scene: number;

};



export type SceneStateFlags = {

  conflict_mode_active: boolean;

  ai_alert_triggered: boolean;

  remaining_player_lore_tokens: number;

};



export type CombatInitiativeEntry = {

  entity_id: string;

  entity_type?: string | null;

  display_name?: string | null;

  initiative_score?: number | null;

  is_active?: boolean;

  hp_current?: number;

  hp_max?: number;

};



export type SceneCombatState = {

  is_active: boolean;

  round: number;

  initiative_order: CombatInitiativeEntry[];

  current_turn_entity_id: string | null;

  conflict_mode_active: boolean;

};



export type SceneState = {

  metadata: SceneMetadata;

  context: SceneContext;

  turn_management: TurnManagement;

  memory_settings: MemorySettings;

  chat_buffer: ChatMessage[];

  state_flags: SceneStateFlags;

  combat: SceneCombatState;

};



export type Scene = {

  id: string;

  campaign_id: string;

  scene_number: number;

  display_name?: string | null;

  status: string;

  summary?: string | null;

  scene_state: SceneState;

};



export type MasterAssistMode = "narrative" | "rules" | "campaign";

export type MasterAssistQueryKind = "rules" | "narrative" | "creative" | "campaign";

export type MasterAssistResponse = {

  query: string;

  context_summary: string;

  suggestions: string[];

  query_kind?: MasterAssistQueryKind;

  note: string;

};



export type EntityType = "NPC" | "PC" | "FACTION" | "LOCATION" | "RELATIONSHIP" | "ARC_MANIFEST";



export type CampaignEntity = {

  id: string;

  campaign_id: string;

  entity_type: EntityType;

  document: Record<string, unknown>;

  created_at: string;

  updated_at: string;

};



export type PcIdentity = {

  name: string;

  concept: string;

  faction_id: string | null;

  current_location_id: string | null;

};



export type PublicProfile = {

  description: string;

  personality_traits: string[];

};



export type TypedSystemMechanics = {

  system_id: string;

  schema_version: string;

  sheet: Record<string, unknown>;

};



export type PcStateFlags = {

  is_present_in_scene: boolean;

  is_incapacitated: boolean;

};



export type CharacterSheetUpsert = {

  identity: PcIdentity;

  public_profile?: PublicProfile | null;

  system_mechanics: TypedSystemMechanics;

  state_flags?: PcStateFlags | null;

};



export type Dnd5eRollType =

  | "ability_check"

  | "saving_throw"

  | "skill_check"

  | "attack_roll"

  | "damage"

  | "initiative";



export type CyberpunkRollType =

  | "skill_check"

  | "stat_check"

  | "attack_roll"

  | "damage"

  | "initiative";



export type VtmRollType =

  | "skill_check"

  | "attribute_check"

  | "rouse_check"

  | "discipline_check";



export type SheetRollType = Dnd5eRollType | CyberpunkRollType | VtmRollType;



export type SheetRollContext = {

  ability?: string;

  skill?: string;

  attack_name?: string;

  attack_index?: number;

  dc?: number;

  target_ac?: number;

  advantage?: boolean;

  disadvantage?: boolean;

  modifier_override?: number;

  expression?: string;

};



export type SheetRollRequest = {

  roll_type: SheetRollType;

  dice_expression?: string;

  modifier?: number;

  context?: SheetRollContext;

};



export type SheetRollResponse = {

  dice_expression: string;

  rolls: number[];

  raw_result: number | null;

  final_result: number | null;

  contextual: boolean;

  game_system: string;

  roll_type: string;

  success: boolean | null;

  roll_details: Record<string, unknown>;

  chat_summary: string;

};

