import { getApiBase } from "./apiBase";
import { http, httpUpload } from "./http";
import type {
  AuthResponse,
  Campaign,
  CampaignDocument,
  CampaignEntity,
  CampaignMember,
  CharacterSheetUpsert,
  CombatAttackRequest,
  ScenePresenceUpdate,
  SheetRollRequest,
  SheetRollResponse,
  DocumentType,
  EntityExportBundle,
  EntityType,
  MasterAssistMode,
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

export type UpdateEntityPayload = {
  document: Record<string, unknown>;
};

export const api = {
  health: () => http<{ status: string }>("/api/v1/health"),
  register: (payload: RegisterPayload) =>
    http<AuthResponse>("/api/v1/auth/register", { method: "POST", body: JSON.stringify(payload) }),
  login: (payload: LoginPayload) =>
    http<AuthResponse>("/api/v1/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  me: () => http<AuthResponse["user"]>("/api/v1/auth/me"),
  updateMe: (displayName: string) =>
    http<AuthResponse["user"]>("/api/v1/auth/me", {
      method: "PATCH",
      body: JSON.stringify({ display_name: displayName }),
    }),
  listCampaigns: () => http<Campaign[]>("/api/v1/campaigns"),
  getCampaign: (campaignId: string) => http<Campaign>(`/api/v1/campaigns/${campaignId}`),
  createCampaign: (payload: CreateCampaignPayload) =>
    http<Campaign>("/api/v1/campaigns", { method: "POST", body: JSON.stringify(payload) }),
  listCampaignMembers: (campaignId: string) =>
    http<CampaignMember[]>(`/api/v1/campaigns/${campaignId}/members`),
  listOocMessages: (campaignId: string) =>
    http<import("./types").OocMessage[]>(`/api/v1/campaigns/${campaignId}/ooc/messages`),
  postOocMessage: (campaignId: string, content: string) =>
    http<import("./types").OocMessage>(`/api/v1/campaigns/${campaignId}/ooc/messages`, {
      method: "POST",
      body: JSON.stringify({ content }),
    }),
  postOocWhisper: (campaignId: string, content: string, targetUserId: string) =>
    http<import("./types").OocMessage>(`/api/v1/campaigns/${campaignId}/ooc/whispers`, {
      method: "POST",
      body: JSON.stringify({ content, target_user_id: targetUserId }),
    }),
  getUnreadCounts: (campaignId: string) =>
    http<import("./types").UnreadCounts>(`/api/v1/campaigns/${campaignId}/unread-counts`),
  markOocRead: (campaignId: string) =>
    http<void>(`/api/v1/campaigns/${campaignId}/ooc/read`, { method: "POST" }),
  inviteMember: (campaignId: string, payload: InviteMemberPayload) =>
    http<CampaignMember>(`/api/v1/campaigns/${campaignId}/members`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getActiveScene: (campaignId: string) => http<Scene>(`/api/v1/campaigns/${campaignId}/scenes/active`),
  listCampaignScenes: (campaignId: string) => http<Scene[]>(`/api/v1/campaigns/${campaignId}/scenes`),
  createScene: (campaignId: string, options?: { sceneObjective?: string; displayName?: string }) =>
    http<Scene>("/api/v1/scenes", {
      method: "POST",
      body: JSON.stringify({
        campaign_id: campaignId,
        scene_objective: options?.sceneObjective,
        display_name: options?.displayName,
      }),
    }),
  getScene: (sceneId: string) => http<Scene>(`/api/v1/scenes/${sceneId}`),
  postMessage: (
    sceneId: string,
    text: string,
    type: string = "ACTION",
    speaker?: {
      speaker_type: string;
      speaker_entity_id?: string;
      speaker_display_name: string;
    },
  ) =>
    http<Scene>(`/api/v1/scenes/${sceneId}/messages`, {
      method: "POST",
      body: JSON.stringify({
        type,
        text,
        ...(speaker ?? {}),
      }),
    }),
  rollDice: (
    sceneId: string,
    diceExpression: string,
    options?: { modifier?: number; advantage?: boolean; disadvantage?: boolean; masterOnly?: boolean },
  ) =>
    http<Scene>(`/api/v1/scenes/${sceneId}/dice`, {
      method: "POST",
      body: JSON.stringify({
        dice_expression: diceExpression,
        modifier: options?.modifier ?? 0,
        advantage: options?.advantage ?? false,
        disadvantage: options?.disadvantage ?? false,
        master_only: options?.masterOnly ?? false,
      }),
    }),
  markSceneRead: (sceneId: string, messageIds?: string[]) =>
    http<Scene>(`/api/v1/scenes/${sceneId}/read`, {
      method: "POST",
      body: JSON.stringify({ message_ids: messageIds ?? null }),
    }),
  activateScene: (campaignId: string, sceneId: string) =>
    http<Scene>(`/api/v1/campaigns/${campaignId}/scenes/${sceneId}/activate`, {
      method: "POST",
    }),
  updateSceneStatus: (sceneId: string, status: "ACTIVE" | "PAUSED") =>
    http<Scene>(`/api/v1/scenes/${sceneId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),
  updateSceneDisplayName: (sceneId: string, displayName: string | null) =>
    http<Scene>(`/api/v1/scenes/${sceneId}`, {
      method: "PATCH",
      body: JSON.stringify({ display_name: displayName }),
    }),
  closeScene: (sceneId: string) =>
    http<Scene>(`/api/v1/scenes/${sceneId}/close`, {
      method: "POST",
    }),
  deleteSceneMessage: (sceneId: string, messageId: string) =>
    http<Scene>(`/api/v1/scenes/${sceneId}/messages/${messageId}`, {
      method: "DELETE",
    }),
  toggleSceneMessageLike: (sceneId: string, messageId: string) =>
    http<Scene>(`/api/v1/scenes/${sceneId}/messages/${messageId}/like`, {
      method: "POST",
    }),
  rollCombatInitiative: (sceneId: string, options?: { activateCombat?: boolean }) =>
    http<Scene>(`/api/v1/scenes/${sceneId}/combat/initiative`, {
      method: "POST",
      body: JSON.stringify({ activate_combat: options?.activateCombat ?? true }),
    }),
  updateSceneTurnManagement: (sceneId: string, payload: import("./types").SceneTurnManagementUpdate) =>
    http<Scene>(`/api/v1/scenes/${sceneId}/turn-management`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  advancePbpTurn: (sceneId: string) =>
    http<Scene>(`/api/v1/scenes/${sceneId}/turn-management/advance`, {
      method: "POST",
    }),
  combatAttack: (sceneId: string, payload: CombatAttackRequest) =>
    http<Scene>(`/api/v1/scenes/${sceneId}/combat/attack`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateScenePresence: (sceneId: string, payload: ScenePresenceUpdate) =>
    http<Scene>(`/api/v1/scenes/${sceneId}/presence`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  addPlayerToScene: (sceneId: string, payload: import("./types").SceneAddPlayerRequest) =>
    http<Scene>(`/api/v1/scenes/${sceneId}/presence/add-player`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  masterAssist: (campaignId: string, sceneId: string, query: string, mode: MasterAssistMode = "campaign") =>
    http<MasterAssistResponse>("/api/v1/master/assist", {
      method: "POST",
      body: JSON.stringify({
        campaign_id: campaignId,
        scene_id: sceneId,
        query,
        mode,
      }),
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
  getMySheet: (campaignId: string) =>
    http<CampaignEntity>(`/api/v1/campaigns/${campaignId}/my-sheet`),
  upsertMySheet: (campaignId: string, payload: CharacterSheetUpsert) =>
    http<CampaignEntity>(`/api/v1/campaigns/${campaignId}/my-sheet`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  rollFromMySheet: (campaignId: string, payload: SheetRollRequest) =>
    http<SheetRollResponse>(`/api/v1/campaigns/${campaignId}/my-sheet/roll`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  rollFromEntitySheet: (entityId: string, payload: SheetRollRequest) =>
    http<SheetRollResponse>(`/api/v1/entities/${entityId}/roll`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listCampaignSheets: (campaignId: string) =>
    http<CampaignEntity[]>(`/api/v1/campaigns/${campaignId}/sheets`),
  updateEntity: (entityId: string, payload: UpdateEntityPayload) =>
    http<CampaignEntity>(`/api/v1/entities/${entityId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  uploadEntityAvatar: (entityId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return httpUpload<CampaignEntity>(`/api/v1/entities/${entityId}/avatar`, form);
  },
  removeEntityAvatar: (entityId: string) =>
    http<void>(`/api/v1/entities/${entityId}/avatar`, { method: "DELETE" }),
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
  documentDownloadUrl: (documentId: string) => `${getApiBase()}/api/v1/documents/${documentId}/download`,
  updateCampaign: (campaignId: string, payload: { name?: string; tone?: string }) =>
    http<Campaign>(`/api/v1/campaigns/${campaignId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  removeCampaignMember: (campaignId: string, userId: string) =>
    http<void>(`/api/v1/campaigns/${campaignId}/members/${userId}`, { method: "DELETE" }),
  loreAssist: (sceneId: string, query: string) =>
    http<import("./types").LoreAssistResponse>(`/api/v1/scenes/${sceneId}/lore-assist`, {
      method: "POST",
      body: JSON.stringify({ query }),
    }),
  getSystemManualStatus: (systemId: string) =>
    http<import("./types").SystemManualStatusResponse>(`/api/v1/system-manuals/${systemId}/status`),
};

export type { AuthResponse, Campaign, CampaignDocument, CampaignEntity, CampaignMember, CharacterSheetUpsert, ChatMessage, Dnd5eRollType, DocumentType, EntityExportBundle, EntityType, MasterAssistMode, MasterAssistResponse, MessageType, OocMessage, OocMessageType, PcIdentity, PublicProfile, PcStateFlags, Scene, SceneState, SheetRollContext, SheetRollRequest, SheetRollResponse, TypedSystemMechanics } from "./types";
export type { AuthUser, MemberRole } from "../types/auth";
