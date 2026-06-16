import { http } from "./http";
import type { MasterAssistResponse, Scene } from "./types";

export const api = {
  health: () => http<{ status: string }>("/api/v1/health"),
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

export type { ChatMessage, MasterAssistResponse, Scene, SceneState } from "./types";
