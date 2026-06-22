import type { CampaignEntity } from "./entityDefaults";

export type CompendiumTier = "story" | "combat" | "archive";

export const COMPENDIUM_TIER_LABELS: Record<CompendiumTier, string> = {
  story: "Relevante",
  combat: "Combate",
  archive: "Archivo",
};

export type WorldViewFilter = "story" | "combat" | "all";

export function isCatalogSpawnedNpc(entity: CampaignEntity): boolean {
  if (entity.entity_type !== "NPC") return false;
  const metadata = entity.document.metadata as { mechanics_enabled?: boolean; system_agnostic?: boolean } | undefined;
  if (metadata?.mechanics_enabled === true) return true;
  const mechanics = entity.document.system_mechanics as { system_id?: string; sheet?: unknown } | undefined;
  return Boolean(mechanics?.system_id && mechanics?.sheet);
}

export function getNpcCompendiumTier(entity: CampaignEntity): CompendiumTier {
  if (entity.entity_type !== "NPC") return "story";
  const flags = entity.document.state_flags as { compendium_tier?: string } | undefined;
  const explicit = flags?.compendium_tier;
  if (explicit === "story" || explicit === "combat" || explicit === "archive") {
    return explicit;
  }
  return isCatalogSpawnedNpc(entity) ? "combat" : "story";
}

export function withNpcCompendiumTier(
  document: Record<string, unknown>,
  tier: CompendiumTier,
): Record<string, unknown> {
  const flags = {
    ...(document.state_flags as Record<string, unknown>),
    compendium_tier: tier,
  };
  return { ...document, state_flags: flags };
}

export function matchesWorldViewFilter(entity: CampaignEntity, filter: WorldViewFilter): boolean {
  if (filter === "all") return true;
  if (entity.entity_type === "ARC_MANIFEST") return false;

  if (entity.entity_type === "NPC") {
    const tier = getNpcCompendiumTier(entity);
    if (filter === "story") return tier === "story" || tier === "archive";
    if (filter === "combat") return tier === "combat";
  }

  if (filter === "story") {
    return entity.entity_type === "LOCATION" || entity.entity_type === "FACTION" || entity.entity_type === "RELATIONSHIP";
  }

  return false;
}
