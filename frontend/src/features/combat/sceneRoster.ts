import type { CampaignEntity } from "../../api/types";
import { getEntityDisplayName } from "../entities/entityDefaults";
import { getCombatState, normalizeSceneState, type SceneStateInput } from "../scene/sceneState";

export type SceneRosterEntry = {
  id: string;
  label: string;
  maskedLabel: string;
  entityType: "PC" | "NPC";
  userId?: string;
  isHiddenFromPlayers: boolean;
  hpLabel: string | null;
};

export const HIDDEN_NPC_LABEL = "Desconocido";
export const HIDDEN_NPC_HINT = "?????";

function getPcUserId(entity: CampaignEntity): string | undefined {
  const binding = entity.document.player_binding as { user_id?: string } | undefined;
  return binding?.user_id;
}

function getNpcHasMetParty(entity: CampaignEntity): boolean {
  const flags = entity.document.state_flags as { has_met_party?: boolean } | undefined;
  return flags?.has_met_party ?? false;
}

export function isNpcHiddenFromPlayer(
  entityId: string,
  entity: CampaignEntity | undefined,
  sceneState: SceneStateInput,
): boolean {
  const normalized = normalizeSceneState(sceneState);
  if (normalized.context.hidden_npc_ids?.includes(entityId)) return true;
  if (entity?.entity_type === "NPC" && !getNpcHasMetParty(entity)) return true;
  return false;
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

function isNpcInScene(
  entity: CampaignEntity,
  sceneState: SceneStateInput,
  initiativeIds: Set<string>,
): boolean {
  const normalized = normalizeSceneState(sceneState);
  return normalized.context.active_npc_ids.includes(entity.id) || initiativeIds.has(entity.id);
}

function readHpLabel(entity: CampaignEntity, initiativeIds: Set<string>, combatHp?: { current?: number; max?: number }): string | null {
  if (combatHp?.current != null && combatHp?.max != null) {
    return `${combatHp.current}/${combatHp.max}`;
  }

  const mechanics = entity.document.system_mechanics as {
    sheet?: { defense?: { hp_current?: number; hp_max?: number } };
  } | undefined;
  const hp = mechanics?.sheet?.defense;
  if (hp?.hp_current != null && hp?.hp_max != null) {
    return `${hp.hp_current}/${hp.hp_max}`;
  }

  if (initiativeIds.has(entity.id)) return null;
  return null;
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

    const inScene =
      entity.entity_type === "PC"
        ? isPcInScene(entity, initiativeIds, turnOrderUserIds)
        : isNpcInScene(entity, sceneState, initiativeIds);

    if (!inScene) continue;

    const realName = getEntityDisplayName(entity);
    const dedupeKey = entity.id;
    if (seen.has(dedupeKey)) continue;
    seen.add(dedupeKey);

    const hiddenFromPlayers = entity.entity_type === "NPC" && isNpcHiddenFromPlayer(entity.id, entity, sceneState);
    const displayName = !isMaster && hiddenFromPlayers ? HIDDEN_NPC_LABEL : realName;
    const maskedLabel = hiddenFromPlayers ? HIDDEN_NPC_HINT : realName;

    entries.push({
      id: entity.id,
      label: displayName,
      maskedLabel,
      entityType: entity.entity_type,
      userId: entity.entity_type === "PC" ? getPcUserId(entity) : undefined,
      isHiddenFromPlayers: hiddenFromPlayers,
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
