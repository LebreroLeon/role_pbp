import type { CampaignEntity, EntityType } from "./entityDefaults";

export type CompendiumTier = "story" | "combat" | "archive";

/** Entity editor / list labels — aligned with world view tab naming. */
export const COMPENDIUM_TIER_LABELS: Record<CompendiumTier, string> = {
  story: "Para jugadores",
  combat: "Para máster",
  archive: "Ambos",
};

/** Master compendium list tabs: story ≈ player-visible narrative, combat ≈ master bestiary, all = both. */
export type WorldViewFilter = "story" | "combat" | "all";

export const WORLD_VIEW_TAB_LABELS: Record<WorldViewFilter, string> = {
  story: "Para jugadores",
  combat: "Para máster",
  all: "Ambos",
};

const COMPENDIUM_TIER_ENTITY_TYPES = new Set<EntityType>([
  "NPC",
  "LOCATION",
  "FACTION",
  "RELATIONSHIP",
]);

export function entityHasCompendiumTier(entity: CampaignEntity): boolean {
  return COMPENDIUM_TIER_ENTITY_TYPES.has(entity.entity_type);
}

export function isCatalogSpawnedNpc(entity: CampaignEntity): boolean {
  if (entity.entity_type !== "NPC") return false;
  const metadata = entity.document.metadata as { mechanics_enabled?: boolean; system_agnostic?: boolean } | undefined;
  if (metadata?.mechanics_enabled === true) return true;
  const mechanics = entity.document.system_mechanics as { system_id?: string; sheet?: unknown } | undefined;
  return Boolean(mechanics?.system_id && mechanics?.sheet);
}

function readExplicitCompendiumTier(document: Record<string, unknown>): CompendiumTier | null {
  const flags = document.state_flags as { compendium_tier?: string } | undefined;
  const explicit = flags?.compendium_tier;
  if (explicit === "story" || explicit === "combat" || explicit === "archive") {
    return explicit;
  }
  return null;
}

export function getCompendiumTier(entity: CampaignEntity): CompendiumTier {
  const explicit = readExplicitCompendiumTier(entity.document);
  if (explicit) return explicit;

  if (entity.entity_type === "NPC") {
    return isCatalogSpawnedNpc(entity) ? "combat" : "story";
  }

  return "story";
}

/** @deprecated Use getCompendiumTier */
export const getNpcCompendiumTier = getCompendiumTier;

export function withCompendiumTier(
  document: Record<string, unknown>,
  tier: CompendiumTier,
): Record<string, unknown> {
  const flags = {
    ...(document.state_flags as Record<string, unknown>),
    compendium_tier: tier,
  };
  return { ...document, state_flags: flags };
}

/** @deprecated Use withCompendiumTier */
export const withNpcCompendiumTier = withCompendiumTier;

function tierMatchesFilter(tier: CompendiumTier, filter: Exclude<WorldViewFilter, "all">): boolean {
  if (tier === "archive") return true;
  return tier === filter;
}

export function matchesWorldViewFilter(entity: CampaignEntity, filter: WorldViewFilter): boolean {
  if (filter === "all") return entity.entity_type !== "ARC_MANIFEST";
  if (entity.entity_type === "ARC_MANIFEST") return false;

  if (entity.entity_type === "PC") {
    return filter === "story";
  }

  if (!entityHasCompendiumTier(entity)) {
    return false;
  }

  return tierMatchesFilter(getCompendiumTier(entity), filter);
}
