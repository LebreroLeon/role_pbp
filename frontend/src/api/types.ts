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
