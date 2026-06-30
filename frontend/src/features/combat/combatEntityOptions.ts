import type { CampaignEntity } from "../../api/types";
import { getEntityDisplayName } from "../entities/entityDefaults";
import { getCombatState, normalizeSceneState, type SceneStateInput } from "../scene/sceneState";

export type CombatEntityOption = {
  id: string;
  label: string;
  entityType: "PC" | "NPC";
  userId?: string;
};

function getPcUserId(entity: CampaignEntity): string | undefined {
  const binding = entity.document.player_binding as { user_id?: string } | undefined;
  return binding?.user_id;
}

function isEntityInScene(
  entity: CampaignEntity,
  sceneState: SceneStateInput,
  initiativeIds: Set<string>,
  turnOrderUserIds: Set<string>,
): boolean {
  if (entity.entity_type === "NPC") {
    const normalized = normalizeSceneState(sceneState);
    return normalized.context.active_npc_ids.includes(entity.id);
  }

  const flags = entity.document.state_flags as { is_present_in_scene?: boolean } | undefined;
  if (flags?.is_present_in_scene) return true;
  if (initiativeIds.has(entity.id)) return true;
  if (initiativeIds.size === 0) return true;

  const userId = getPcUserId(entity);
  if (userId && turnOrderUserIds.has(userId)) return true;

  return false;
}

export function buildCombatEntityOptions(
  sceneState: SceneStateInput | null | undefined,
  entities: CampaignEntity[] | undefined,
): CombatEntityOption[] {
  if (!sceneState || !entities?.length) return [];

  const normalized = normalizeSceneState(sceneState);
  const combat = getCombatState(normalized);
  const initiativeIds = new Set(combat.initiative_order.map((entry) => entry.entity_id));
  const turnOrderUserIds = new Set(normalized.turn_management.turn_order);
  const options: CombatEntityOption[] = [];
  const seen = new Set<string>();

  for (const entity of entities) {
    if (entity.entity_type !== "PC" && entity.entity_type !== "NPC") continue;
    if (!isEntityInScene(entity, sceneState, initiativeIds, turnOrderUserIds)) continue;

    const label = getEntityDisplayName(entity);
    const key = label.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);

    options.push({
      id: entity.id,
      label,
      entityType: entity.entity_type,
      userId: entity.entity_type === "PC" ? getPcUserId(entity) : undefined,
    });
  }

  return options.sort((a, b) => a.label.localeCompare(b.label, "es"));
}

export function findPlayerPcOption(
  options: CombatEntityOption[],
  currentUserId: string,
): CombatEntityOption | null {
  return options.find((option) => option.entityType === "PC" && option.userId === currentUserId) ?? null;
}

type SheetAttack = {
  name?: string;
  ability?: string;
  proficient?: boolean;
  resolution?: "attack_roll" | "save";
  half_damage_on_save?: boolean;
  effect_type?: "damage" | "healing";
  damage?: { dice?: string; type?: string };
};

type EntitySheet = {
  abilities?: Record<string, number>;
  proficiency?: { bonus?: number };
  proficiency_bonus?: number;
  spellcasting?: { ability?: string; save_dc?: number | null };
  attacks?: SheetAttack[];
};

export type CombatAttackOption = {
  name: string;
  statsLabel: string | null;
};

function formatSigned(value: number): string {
  return value >= 0 ? `+${value}` : `${value}`;
}

function abilityModifier(score: number): number {
  return Math.floor((score - 10) / 2);
}

function computedSpellSaveDc(sheet: EntitySheet | undefined): number | null {
  const spellcasting = sheet?.spellcasting;
  if (!spellcasting) return null;
  if (typeof spellcasting.save_dc === "number") return spellcasting.save_dc;
  const ability = spellcasting.ability;
  const abilityScore = ability ? sheet?.abilities?.[ability] : undefined;
  const proficiencyBonus = sheet?.proficiency?.bonus ?? sheet?.proficiency_bonus ?? 0;
  if (typeof abilityScore !== "number") return null;
  return 8 + proficiencyBonus + abilityModifier(abilityScore);
}

function buildAttackStatsLabel(attack: SheetAttack, sheet: EntitySheet | undefined): string | null {
  const parts: string[] = [];

  if (attack.resolution === "save") {
    const ability = attack.ability;
    if (ability) {
      parts.push(`Salv. ${ability.toUpperCase()}`);
    }
    const saveDc = computedSpellSaveDc(sheet);
    if (saveDc != null) {
      parts.push(`CD ${saveDc}`);
    }
  } else {
    const ability = attack.ability;
    const abilityScore = ability ? sheet?.abilities?.[ability] : undefined;
    if (typeof abilityScore === "number") {
      const modifier = abilityModifier(abilityScore);
      const proficiencyBonus = sheet?.proficiency?.bonus ?? sheet?.proficiency_bonus ?? 0;
      const toHit = modifier + (attack.proficient ? proficiencyBonus : 0);
      parts.push(formatSigned(toHit));
    }
  }

  const dice = attack.damage?.dice?.trim();
  const damageType = attack.damage?.type?.trim();
  if (dice) {
    parts.push(damageType ? `${dice} ${damageType}` : dice);
  }
  if (attack.resolution === "save" && attack.half_damage_on_save) {
    parts.push("½ si salva");
  }

  return parts.length > 0 ? parts.join(" · ") : null;
}

export function extractAttacksFromEntity(entity: CampaignEntity | null | undefined): CombatAttackOption[] {
  if (!entity) return [];
  const mechanics = entity.document.system_mechanics as { sheet?: EntitySheet } | undefined;
  const sheet = mechanics?.sheet;
  const attacks = sheet?.attacks;
  if (!Array.isArray(attacks)) return [];
  return attacks
    .map((attack, index) => ({
      name: attack.name?.trim() || `Ataque ${index + 1}`,
      statsLabel: buildAttackStatsLabel(attack, sheet),
    }))
    .filter((attack) => attack.name.length > 0);
}
