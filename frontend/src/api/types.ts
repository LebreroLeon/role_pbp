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

export type MessageType = "SPEAK" | "ACTION" | "CONTEXT" | "MASTER" | "DICE_ROLL" | "NARRATIVE";

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
};

export type SceneState = {
  campaign_id: string;
  status: string;
  scene_objective?: string;
  chat_buffer: ChatMessage[];
};

export type Scene = {
  id: string;
  campaign_id: string;
  status: string;
  scene_state: SceneState;
};

export type MasterAssistResponse = {
  query: string;
  context_summary: string;
  suggestions: string[];
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
