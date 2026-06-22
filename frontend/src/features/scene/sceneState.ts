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
  master_prep_notes?: string | null;
  opening_narration?: string | null;
  prepared_entity_refs?: import("../../api/types").PreparedEntityRef[];
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

const DEFAULT_TURN_MANAGEMENT = {
  current_turn_player_id: null as string | null,
  turn_order: [] as string[],
  pbp_enabled: false,
  order_source: "manual" as const,
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
    const turnManagement = raw.turn_management;
    return {
      ...raw,
      context: { ...raw.context, hidden_npc_ids: raw.context.hidden_npc_ids ?? [], prepared_entity_refs: raw.context.prepared_entity_refs ?? [] },
      turn_management: {
        ...turnManagement,
        pbp_enabled: turnManagement.pbp_enabled ?? false,
        order_source: turnManagement.order_source ?? "manual",
      },
    };
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
      master_prep_notes: flat.master_prep_notes ?? null,
      opening_narration: flat.opening_narration ?? null,
      prepared_entity_refs: flat.prepared_entity_refs ?? [],
    },
    turn_management: {
      ...DEFAULT_TURN_MANAGEMENT,
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

export function isPbpEnabled(state: SceneStateInput): boolean {
  return normalizeSceneState(state).turn_management.pbp_enabled;
}

export function getOrderSource(state: SceneStateInput) {
  return normalizeSceneState(state).turn_management.order_source;
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

export function getCurrentTurnEntityId(state: SceneStateInput): string | null {
  const normalized = normalizeSceneState(state);
  if (normalized.combat.initiative_order.length > 0) {
    return (
      normalized.combat.current_turn_entity_id ??
      normalized.combat.initiative_order[0]?.entity_id ??
      null
    );
  }
  return null;
}

export function canUserPostInPbp(
  state: SceneStateInput,
  currentUserId: string,
  isMaster: boolean,
  entities: { id: string; entity_type: string; document: Record<string, unknown> }[],
): boolean {
  if (isMaster || !isPbpEnabled(state)) return true;

  const normalized = normalizeSceneState(state);
  const initiativeOrder = normalized.combat.initiative_order;

  if (initiativeOrder.length > 0) {
    const currentEntityId = getCurrentTurnEntityId(state);
    if (!currentEntityId) return true;
    const pc = entities.find((entity) => {
      if (entity.entity_type !== "PC") return false;
      const binding = entity.document.player_binding as { user_id?: string } | undefined;
      return binding?.user_id === currentUserId;
    });
    return pc?.id === currentEntityId;
  }

  const currentPlayerId = normalized.turn_management.current_turn_player_id;
  if (!currentPlayerId) return true;
  return currentPlayerId === currentUserId;
}

const HIDDEN_NPC_LABEL = "Desconocido";

function formatTurnHolderLabel(characterName: string, playerDisplayName?: string | null): string {
  if (playerDisplayName?.trim()) {
    return `${characterName} (${playerDisplayName.trim()})`;
  }
  return characterName;
}

function readEntityName(
  entity: { id: string; entity_type: string; document: Record<string, unknown> },
  _state: SceneStateInput,
  isMaster: boolean,
): string {
  if (entity.entity_type === "NPC" && !isMaster) {
    const flags = entity.document.state_flags as { player_visibility?: string; hidden_from_players?: boolean } | undefined;
    const visibility = flags?.player_visibility ?? (flags?.hidden_from_players ? "hidden" : "visible");
    if (visibility === "unknown") return HIDDEN_NPC_LABEL;
  }
  const identity = entity.document.identity as { name?: string } | undefined;
  if (identity?.name?.trim()) return identity.name.trim();
  return entity.id.slice(0, 8);
}

function readPcPlayerName(
  entity: { document: Record<string, unknown> },
  members: Record<string, { display_name: string } | undefined>,
): string | undefined {
  const binding = entity.document.player_binding as { user_id?: string } | undefined;
  const userId = binding?.user_id;
  return userId ? members[userId]?.display_name : undefined;
}

export function resolveCurrentTurnLabel(
  state: SceneStateInput,
  members: Record<string, { display_name: string } | undefined>,
  entities: { id: string; entity_type: string; document: Record<string, unknown> }[],
  isMaster = false,
): string | null {
  const normalized = normalizeSceneState(state);

  if (normalized.combat.initiative_order.length > 0) {
    const currentEntityId = getCurrentTurnEntityId(state);
    if (!currentEntityId) return null;

    const entity = entities.find((item) => item.id === currentEntityId);
    if (entity) {
      const characterName = readEntityName(entity, state, isMaster);
      if (entity.entity_type === "PC") {
        return formatTurnHolderLabel(characterName, readPcPlayerName(entity, members));
      }
      return characterName;
    }

    const entry = normalized.combat.initiative_order.find((item) => item.entity_id === currentEntityId);
    if (entry) {
      const characterName = entry.display_name?.trim() || currentEntityId.slice(0, 8);
      if (entry.entity_type === "PC") {
        const pc = entities.find((item) => item.id === currentEntityId);
        return formatTurnHolderLabel(characterName, pc ? readPcPlayerName(pc, members) : undefined);
      }
      return characterName;
    }
    return null;
  }

  const currentPlayerId = normalized.turn_management.current_turn_player_id;
  if (!currentPlayerId) return null;

  const playerDisplayName = members[currentPlayerId]?.display_name;
  const pc = entities.find((entity) => {
    if (entity.entity_type !== "PC") return false;
    const binding = entity.document.player_binding as { user_id?: string } | undefined;
    return binding?.user_id === currentPlayerId;
  });

  if (pc) {
    return formatTurnHolderLabel(readEntityName(pc, state, isMaster), playerDisplayName);
  }

  return playerDisplayName ?? currentPlayerId.slice(0, 8);
}
