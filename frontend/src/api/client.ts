import { http, httpUpload } from "./http";
import type {
  AuthResponse,
  Campaign,
  CampaignDocument,
  CampaignEntity,
  CampaignMember,
  DocumentType,
  EntityExportBundle,
  EntityType,
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
  game_system?: string;
};

export type InviteMemberPayload = {
  email: string;
  role?: "MASTER" | "PLAYER";
};

export type CreateEntityPayload = {
  entity_type: EntityType;
  document: Record<string, unknown>;
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
  getActiveScene: (campaignId: string) => http<Scene>(`/api/v1/campaigns/${campaignId}/scenes/active`),
  createScene: (campaignId: string, sceneObjective?: string) =>
    http<Scene>("/api/v1/scenes", {
      method: "POST",
      body: JSON.stringify({
        campaign_id: campaignId,
        scene_objective: sceneObjective,
      }),
    }),
  getScene: (sceneId: string) => http<Scene>(`/api/v1/scenes/${sceneId}`),
  postMessage: (sceneId: string, text: string, type: string = "ACTION") =>
    http<Scene>(`/api/v1/scenes/${sceneId}/messages`, {
      method: "POST",
      body: JSON.stringify({ type, text }),
    }),
  rollDice: (sceneId: string, diceExpression: string) =>
    http<Scene>(`/api/v1/scenes/${sceneId}/dice`, {
      method: "POST",
      body: JSON.stringify({ dice_expression: diceExpression }),
    }),
  markSceneRead: (sceneId: string, messageIds?: string[]) =>
    http<Scene>(`/api/v1/scenes/${sceneId}/read`, {
      method: "POST",
      body: JSON.stringify({ message_ids: messageIds ?? null }),
    }),
  updateSceneStatus: (sceneId: string, status: "ACTIVE" | "PAUSED") =>
    http<Scene>(`/api/v1/scenes/${sceneId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),
  masterAssist: (campaignId: string, sceneId: string, query: string) =>
    http<MasterAssistResponse>("/api/v1/master/assist", {
      method: "POST",
      body: JSON.stringify({ campaign_id: campaignId, scene_id: sceneId, query }),
    }),
  listEntities: (campaignId: string, entityType?: EntityType) => {
    const params = new URLSearchParams({ campaign_id: campaignId });
    if (entityType) params.set("entity_type", entityType);
    return http<CampaignEntity[]>(`/api/v1/entities?${params.toString()}`);
  },
  createEntity: (campaignId: string, payload: CreateEntityPayload) =>
    http<CampaignEntity>("/api/v1/entities", {
      method: "POST",
      body: JSON.stringify({ campaign_id: campaignId, ...payload }),
    }),
  deleteEntity: (entityId: string) =>
    http<void>(`/api/v1/entities/${entityId}`, { method: "DELETE" }),
  exportEntities: (campaignId: string) =>
    http<EntityExportBundle>(`/api/v1/entities/export?campaign_id=${campaignId}`),
  importEntities: (campaignId: string, entities: EntityExportBundle["entities"]) =>
    http<{ created: number; entities: CampaignEntity[] }>("/api/v1/entities/import", {
      method: "POST",
      body: JSON.stringify({ campaign_id: campaignId, entities }),
    }),
  listDocuments: (campaignId: string) =>
    http<CampaignDocument[]>(`/api/v1/documents?campaign_id=${campaignId}`),
  uploadDocument: (campaignId: string, file: File, documentType: DocumentType) => {
    const form = new FormData();
    form.append("campaign_id", campaignId);
    form.append("document_type", documentType);
    form.append("file", file);
    return httpUpload<CampaignDocument>("/api/v1/documents", form);
  },
  deleteDocument: (documentId: string) =>
    http<void>(`/api/v1/documents/${documentId}`, { method: "DELETE" }),
  documentDownloadUrl: (documentId: string) => `${import.meta.env.VITE_API_URL ?? ""}/api/v1/documents/${documentId}/download`,
};

export type { AuthResponse, Campaign, CampaignDocument, CampaignEntity, CampaignMember, ChatMessage, DocumentType, EntityExportBundle, EntityType, MasterAssistResponse, MessageType, Scene, SceneState } from "./types";
export type { AuthUser, MemberRole } from "../types/auth";
