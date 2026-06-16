import { http } from "./http";
import type {
  AuthResponse,
  Campaign,
  CampaignMember,
  MasterAssistResponse,
  Scene,
} from "./types";

export type RegisterPayload = {
  email: string;
  password: string;
  display_name: string;
};

export type LoginPayload = {
  email: string;
  password: string;
};

export type CreateCampaignPayload = {
  name: string;
  tone?: string;
};

export type InviteMemberPayload = {
  email: string;
  role?: "MASTER" | "PLAYER";
};

export const api = {
  health: () => http<{ status: string }>("/api/v1/health"),
  register: (payload: RegisterPayload) =>
    http<AuthResponse>("/api/v1/auth/register", { method: "POST", body: JSON.stringify(payload) }),
  login: (payload: LoginPayload) =>
    http<AuthResponse>("/api/v1/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  me: () => http<AuthResponse["user"]>("/api/v1/auth/me"),
  listCampaigns: () => http<Campaign[]>("/api/v1/campaigns"),
  getCampaign: (campaignId: string) => http<Campaign>(`/api/v1/campaigns/${campaignId}`),
  createCampaign: (payload: CreateCampaignPayload) =>
    http<Campaign>("/api/v1/campaigns", { method: "POST", body: JSON.stringify(payload) }),
  listCampaignMembers: (campaignId: string) =>
    http<CampaignMember[]>(`/api/v1/campaigns/${campaignId}/members`),
  inviteMember: (campaignId: string, payload: InviteMemberPayload) =>
    http<CampaignMember>(`/api/v1/campaigns/${campaignId}/members`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  createScene: (campaignId: string, sceneObjective?: string) =>
    http<Scene>("/api/v1/scenes", {
      method: "POST",
      body: JSON.stringify({
        campaign_id: campaignId,
        scene_objective: sceneObjective,
        turn_order: ["player_1", "master"],
      }),
    }),
  getScene: (sceneId: string) => http<Scene>(`/api/v1/scenes/${sceneId}`),
  postMessage: (sceneId: string, senderId: string, text: string) =>
    http<Scene>(`/api/v1/scenes/${sceneId}/messages`, {
      method: "POST",
      body: JSON.stringify({ sender_id: senderId, type: "NARRATIVE", text }),
    }),
  rollDice: (sceneId: string, senderId: string, diceExpression: string) =>
    http<Scene>(`/api/v1/scenes/${sceneId}/dice`, {
      method: "POST",
      body: JSON.stringify({ sender_id: senderId, dice_expression: diceExpression }),
    }),
  masterAssist: (campaignId: string, sceneId: string, query: string) =>
    http<MasterAssistResponse>("/api/v1/master/assist", {
      method: "POST",
      body: JSON.stringify({ campaign_id: campaignId, scene_id: sceneId, query }),
    }),
};

export type { AuthResponse, Campaign, CampaignMember, ChatMessage, MasterAssistResponse, Scene, SceneState } from "./types";
export type { AuthUser, MemberRole } from "../types/auth";
