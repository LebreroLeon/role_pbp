import type {
  ChatMessage,
  MemorySettings,
  Scene,
  SceneCombatState,
  SceneState,
  SceneStateFlags,
  SceneStatusType,
} from "../../api/types";

/** Pre–Phase 0 flat shape kept for cached WS/API payloads. */
export type LegacyFlatSceneState = {
  campaign_id?: string;
  status?: string;
  location_id?: string | null;
  active_npc_ids?: string[];
  hidden_npc_ids?: string[];
  scene_objective?: string | null;
  current_turn_player_id?: string | null;
  turn_order?: string[];
  memory_settings?: Partial<MemorySettings>;
  chat_buffer?: ChatMessage[];
  state_flags?: Partial<SceneStateFlags>;
  combat?: Partial<SceneCombatState & { current_turn_index?: number }>;
};

export type SceneStateInput = SceneState | LegacyFlatSceneState;

const DEFAULT_MEMORY_SETTINGS: MemorySettings = {
  max_chat_buffer_size: 20,
  rag_top_k_matches: 3,
  max_player_lore_queries_per_scene: 3,
};

const DEFAULT_STATE_FLAGS: SceneStateFlags = {
  conflict_mode_active: false,
  ai_alert_triggered: false,
  remaining_player_lore_tokens: 3,
};

const DEFAULT_COMBAT: SceneCombatState = {
  is_active: false,
  round: 0,
  initiative_order: [],
  current_turn_entity_id: null,
  conflict_mode_active: false,
};

export function isNestedSceneState(state: unknown): state is SceneState {
  return typeof state === "object" && state !== null && "metadata" in state && "context" in state;
}

function normalizeCombat(combat?: LegacyFlatSceneState["combat"]): SceneCombatState {
  if (!combat) return { ...DEFAULT_COMBAT };

  let currentTurnEntityId = combat.current_turn_entity_id ?? null;
  if (
    currentTurnEntityId == null &&
    combat.current_turn_index != null &&
    combat.initiative_order?.length
  ) {
    currentTurnEntityId = combat.initiative_order[combat.current_turn_index]?.entity_id ?? null;
  }

  return {
    is_active: combat.is_active ?? false,
    round: combat.round ?? 0,
    initiative_order: combat.initiative_order ?? [],
    current_turn_entity_id: currentTurnEntityId,
    conflict_mode_active: combat.conflict_mode_active ?? false,
  };
}

export function normalizeSceneState(raw: SceneStateInput): SceneState {
  if (isNestedSceneState(raw)) {
    if (!raw.context.hidden_npc_ids) {
      return {
        ...raw,
        context: { ...raw.context, hidden_npc_ids: [] },
      };
    }
    return raw;
  }

  const flat = raw as LegacyFlatSceneState;
  return {
    metadata: {
      campaign_id: flat.campaign_id ?? "",
      status: (flat.status as SceneStatusType | undefined) ?? "ACTIVE",
    },
    context: {
      location_id: flat.location_id ?? null,
      active_npc_ids: flat.active_npc_ids ?? [],
      hidden_npc_ids: flat.hidden_npc_ids ?? [],
      scene_objective: flat.scene_objective ?? null,
    },
    turn_management: {
      current_turn_player_id: flat.current_turn_player_id ?? null,
      turn_order: flat.turn_order ?? [],
    },
    memory_settings: { ...DEFAULT_MEMORY_SETTINGS, ...flat.memory_settings },
    chat_buffer: flat.chat_buffer ?? [],
    state_flags: { ...DEFAULT_STATE_FLAGS, ...flat.state_flags },
    combat: normalizeCombat(flat.combat),
  };
}

export function normalizeScene(scene: Scene): Scene {
  return {
    ...scene,
    scene_state: normalizeSceneState(scene.scene_state),
  };
}

export function getChatBuffer(state: SceneStateInput): ChatMessage[] {
  return normalizeSceneState(state).chat_buffer;
}

export function getSceneObjective(state: SceneStateInput): string | null {
  return normalizeSceneState(state).context.scene_objective;
}

export function getTurnOrder(state: SceneStateInput): string[] {
  return normalizeSceneState(state).turn_management.turn_order;
}

export function getCurrentTurnPlayerId(state: SceneStateInput): string | null {
  return normalizeSceneState(state).turn_management.current_turn_player_id;
}

export function getCombatState(state: SceneStateInput): SceneCombatState {
  return normalizeSceneState(state).combat;
}

export function isConflictModeActive(state: SceneStateInput): boolean {
  const normalized = normalizeSceneState(state);
  return normalized.state_flags.conflict_mode_active || normalized.combat.conflict_mode_active;
}

export function getCurrentCombatTurnIndex(combat: SceneCombatState): number {
  if (!combat.current_turn_entity_id) return 0;
  const index = combat.initiative_order.findIndex(
    (entry) => entry.entity_id === combat.current_turn_entity_id,
  );
  return index >= 0 ? index : 0;
}
