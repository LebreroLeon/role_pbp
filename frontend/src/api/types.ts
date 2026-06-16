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
  role: "MASTER" | "PLAYER";
};

export type CampaignMember = {
  user_id: string;
  email: string;
  display_name: string;
  role: "MASTER" | "PLAYER";
};

export type ChatMessage = {
  timestamp: string;
  sender_id: string;
  type: string;
  text?: string;
  final_result?: number;
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
