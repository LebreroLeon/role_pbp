import type { MasterAssistResponse, Scene } from "./types";

const API_BASE = import.meta.env.VITE_API_URL ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string }>("/api/v1/health"),
  createScene: (campaignId: string, sceneObjective?: string) =>
    request<Scene>("/api/v1/scenes", {
      method: "POST",
      body: JSON.stringify({
        campaign_id: campaignId,
        scene_objective: sceneObjective,
        turn_order: ["player_1", "master"],
      }),
    }),
  getScene: (sceneId: string) => request<Scene>(`/api/v1/scenes/${sceneId}`),
  postMessage: (sceneId: string, senderId: string, text: string) =>
    request<Scene>(`/api/v1/scenes/${sceneId}/messages`, {
      method: "POST",
      body: JSON.stringify({ sender_id: senderId, type: "NARRATIVE", text }),
    }),
  rollDice: (sceneId: string, senderId: string, diceExpression: string) =>
    request<Scene>(`/api/v1/scenes/${sceneId}/dice`, {
      method: "POST",
      body: JSON.stringify({ sender_id: senderId, dice_expression: diceExpression }),
    }),
  masterAssist: (campaignId: string, sceneId: string, query: string) =>
    request<MasterAssistResponse>("/api/v1/master/assist", {
      method: "POST",
      body: JSON.stringify({ campaign_id: campaignId, scene_id: sceneId, query }),
    }),
};

export type { ChatMessage, MasterAssistResponse, Scene, SceneState } from "./types";
