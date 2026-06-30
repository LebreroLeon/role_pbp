import type { CampaignEntity, CombatInitiativeEntry } from "../../api/types";
import {
  getEntityDisplayName,
  getNpcPlayerVisibility,
  isNpcMaskedForPlayer,
  isNpcWorldHidden,
  NPC_VISIBILITY_LABELS,
  type NpcPlayerVisibility,
} from "../entities/entityDefaults";
import { getCombatState, normalizeSceneState, type SceneStateInput } from "../scene/sceneState";

export type { NpcPlayerVisibility };

export type SceneRosterEntry = {
  id: string;
  label: string;
  entityType: "PC" | "NPC";
  userId?: string;
  playerVisibility: NpcPlayerVisibility | null;
  /** Master badge label in Spanish. */
  playerVisibilityLabel: string | null;
  hpLabel: string | null;
};

export const HIDDEN_NPC_LABEL = "Desconocido";

/** Scene display name: master always sees real name; players see Desconocido when unknown. */
export function resolveSceneEntityDisplayName(
  entity: CampaignEntity,
  _sceneState: SceneStateInput,
  isMaster: boolean,
): string {
  if (!isMaster && entity.entity_type === "NPC" && isNpcMaskedForPlayer(entity)) {
    return HIDDEN_NPC_LABEL;
  }
  return getEntityDisplayName(entity);
}

function getPcUserId(entity: CampaignEntity): string | undefined {
  const binding = entity.document.player_binding as { user_id?: string } | undefined;
  return binding?.user_id;
}

export function isNpcHiddenFromPlayer(entity: CampaignEntity): boolean {
  return isNpcWorldHidden(entity);
}

function isPcInScene(
  entity: CampaignEntity,
  initiativeIds: Set<string>,
  turnOrderUserIds: Set<string>,
): boolean {
  const flags = entity.document.state_flags as { is_present_in_scene?: boolean } | undefined;
  if (flags?.is_present_in_scene) return true;
  if (initiativeIds.has(entity.id)) return true;
  if (initiativeIds.size === 0) return true;

  const userId = getPcUserId(entity);
  if (userId && turnOrderUserIds.has(userId)) return true;

  return false;
}

function isNpcInScene(entity: CampaignEntity, sceneState: SceneStateInput): boolean {
  const normalized = normalizeSceneState(sceneState);
  return normalized.context.active_npc_ids.includes(entity.id);
}

function readEntityHp(entity: CampaignEntity): { current: number; max: number } | null {
  const mechanics = entity.document.system_mechanics as {
    sheet?: {
      hp?: { current?: number; max?: number };
      defense?: { hp?: { current?: number; max?: number } };
    };
  } | undefined;
  const sheet = mechanics?.sheet;
  if (!sheet) return null;

  const nested = sheet.defense?.hp;
  if (nested?.current != null && nested?.max != null) {
    return { current: nested.current, max: nested.max };
  }

  const flat = sheet.hp;
  if (flat?.current != null && flat?.max != null) {
    return { current: flat.current, max: flat.max };
  }

  return null;
}

function readHpLabel(entity: CampaignEntity, initiativeIds: Set<string>, combatHp?: { current?: number; max?: number }): string | null {
  if (combatHp?.current != null && combatHp?.max != null) {
    return `${combatHp.current}/${combatHp.max}`;
  }

  const hp = readEntityHp(entity);
  if (hp) {
    return `${hp.current}/${hp.max}`;
  }

  if (initiativeIds.has(entity.id)) return null;
  return null;
}

export type ResolvedInitiativeEntry = {
  label: string;
  entityType: "PC" | "NPC" | null;
};

export function resolveInitiativeEntryDisplay(
  entry: CombatInitiativeEntry,
  entities: CampaignEntity[] | undefined,
  sceneState: SceneStateInput,
  isMaster: boolean,
): ResolvedInitiativeEntry {
  const entity = entities?.find((item) => item.id === entry.entity_id);
  const entityType = (entry.entity_type ?? entity?.entity_type) as "PC" | "NPC" | undefined;

  if (entity) {
    const label = resolveSceneEntityDisplayName(entity, sceneState, isMaster);
    return { label, entityType: entity.entity_type as "PC" | "NPC" };
  }

  if (entry.display_name?.trim()) {
    return { label: entry.display_name.trim(), entityType: entityType ?? null };
  }

  const pcByUser = entities?.find((item) => {
    if (item.entity_type !== "PC") return false;
    const binding = item.document.player_binding as { user_id?: string } | undefined;
    return binding?.user_id === entry.entity_id;
  });
  if (pcByUser) {
    return { label: getEntityDisplayName(pcByUser), entityType: "PC" };
  }

  return { label: entry.entity_id.slice(0, 8), entityType: entityType ?? null };
}

export function enrichInitiativeEntry(
  entry: CombatInitiativeEntry,
  entities: CampaignEntity[] | undefined,
  sceneState: SceneStateInput,
  isMaster: boolean,
): CombatInitiativeEntry {
  const resolved = resolveInitiativeEntryDisplay(entry, entities, sceneState, isMaster);
  return {
    ...entry,
    display_name: resolved.label,
    entity_type: resolved.entityType ?? entry.entity_type,
  };
}

export function buildSceneRoster(
  sceneState: SceneStateInput | null | undefined,
  entities: CampaignEntity[] | undefined,
  isMaster: boolean,
): SceneRosterEntry[] {
  if (!sceneState || !entities?.length) return [];

  const normalized = normalizeSceneState(sceneState);
  const combat = getCombatState(normalized);
  const initiativeIds = new Set(combat.initiative_order.map((entry) => entry.entity_id));
  const turnOrderUserIds = new Set(normalized.turn_management.turn_order);
  const combatHpById = new Map(
    combat.initiative_order.map((entry) => [
      entry.entity_id,
      { current: entry.hp_current, max: entry.hp_max },
    ]),
  );

  const entries: SceneRosterEntry[] = [];
  const seen = new Set<string>();

  for (const entity of entities) {
    if (entity.entity_type !== "PC" && entity.entity_type !== "NPC") continue;
    if (!isMaster && entity.entity_type === "NPC" && isNpcHiddenFromPlayer(entity)) continue;

    const inScene =
      entity.entity_type === "PC"
        ? isPcInScene(entity, initiativeIds, turnOrderUserIds)
        : isNpcInScene(entity, sceneState);

    if (!inScene) continue;

    const dedupeKey = entity.id;
    if (seen.has(dedupeKey)) continue;
    seen.add(dedupeKey);

    const visibility = entity.entity_type === "NPC" ? getNpcPlayerVisibility(entity) : null;

    entries.push({
      id: entity.id,
      label: resolveSceneEntityDisplayName(entity, sceneState, isMaster),
      entityType: entity.entity_type,
      userId: entity.entity_type === "PC" ? getPcUserId(entity) : undefined,
      playerVisibility: visibility,
      playerVisibilityLabel: visibility ? NPC_VISIBILITY_LABELS[visibility] : null,
      hpLabel: readHpLabel(entity, initiativeIds, combatHpById.get(entity.id)),
    });
  }

  return entries.sort((a, b) => {
    if (a.entityType !== b.entityType) return a.entityType === "PC" ? -1 : 1;
    return a.label.localeCompare(b.label, "es");
  });
}

export function getOffSceneNpcs(
  sceneState: SceneStateInput | null | undefined,
  entities: CampaignEntity[] | undefined,
): CampaignEntity[] {
  if (!sceneState || !entities?.length) return [];

  const normalized = normalizeSceneState(sceneState);
  const combat = getCombatState(normalized);
  const initiativeIds = new Set(combat.initiative_order.map((entry) => entry.entity_id));
  const activeIds = new Set(normalized.context.active_npc_ids);

  return entities
    .filter((entity) => entity.entity_type === "NPC")
    .filter((entity) => !activeIds.has(entity.id) && !initiativeIds.has(entity.id))
    .sort((a, b) => getEntityDisplayName(a).localeCompare(getEntityDisplayName(b), "es"));
}

/** Scene roster entries not yet in the initiative / turn track. */
export function getSceneRosterNotInInitiative(
  sceneState: SceneStateInput | null | undefined,
  entities: CampaignEntity[] | undefined,
  isMaster: boolean,
  trackEntityIds: Iterable<string>,
): SceneRosterEntry[] {
  const trackIds = new Set(trackEntityIds);
  return buildSceneRoster(sceneState, entities, isMaster).filter((entry) => !trackIds.has(entry.id));
}

export function rosterEntryToInitiativeEntry(rosterEntry: SceneRosterEntry): CombatInitiativeEntry {
  return {
    entity_id: rosterEntry.id,
    display_name: rosterEntry.label,
    entity_type: rosterEntry.entityType,
  };
}

export function getOffScenePcs(
  sceneState: SceneStateInput | null | undefined,
  entities: CampaignEntity[] | undefined,
): CampaignEntity[] {
  if (!sceneState || !entities?.length) return [];

  const normalized = normalizeSceneState(sceneState);
  const combat = getCombatState(normalized);
  const initiativeIds = new Set(combat.initiative_order.map((entry) => entry.entity_id));
  const turnOrderUserIds = new Set(normalized.turn_management.turn_order);

  return entities
    .filter((entity) => entity.entity_type === "PC")
    .filter((entity) => !isPcInScene(entity, initiativeIds, turnOrderUserIds))
    .sort((a, b) => getEntityDisplayName(a).localeCompare(getEntityDisplayName(b), "es"));
}
