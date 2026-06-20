import { buildPcDocumentWithSheet, defaultSheetForGameSystem } from "../character-sheet/pcDocument";

export type EntityType = "NPC" | "PC" | "FACTION" | "LOCATION" | "RELATIONSHIP" | "ARC_MANIFEST";

export type CampaignEntity = {
  id: string;
  campaign_id: string;
  entity_type: EntityType;
  document: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export const ENTITY_TYPE_LABELS: Record<EntityType, string> = {
  NPC: "Personaje no jugador",
  PC: "Personaje jugador",
  FACTION: "Facción",
  LOCATION: "Ubicación",
  RELATIONSHIP: "Relación",
  ARC_MANIFEST: "Arco narrativo",
};

export const PLACEHOLDER_UUID = "00000000-0000-0000-0000-000000000001";

/** Legacy placeholder refs should behave as unset in the UI. */
export function normalizeEntityRefId(value: string | null | undefined): string {
  if (!value || value === PLACEHOLDER_UUID) return "";
  return value;
}

export function isNpcWorldHidden(entity: CampaignEntity): boolean {
  if (entity.entity_type !== "NPC") return false;
  const flags = entity.document.state_flags as { hidden_from_players?: boolean } | undefined;
  return Boolean(flags?.hidden_from_players);
}

export function getEntityDisplayName(entity: CampaignEntity, allEntities?: CampaignEntity[]): string {
  if (entity.entity_type === "RELATIONSHIP") {
    const connection = entity.document.connection as
      | { source_id?: string; target_id?: string }
      | undefined;
    const bond = entity.document.narrative_bond as
      | { bond_type?: string; public_status?: string }
      | undefined;
    if (allEntities && connection?.source_id && connection?.target_id) {
      const source = allEntities.find((item) => item.id === connection.source_id);
      const target = allEntities.find((item) => item.id === connection.target_id);
      const sourceName = source ? getEntityDisplayName(source, allEntities) : connection.source_id.slice(0, 8);
      const targetName = target ? getEntityDisplayName(target, allEntities) : connection.target_id.slice(0, 8);
      const bondLabel = bond?.bond_type ?? "vínculo";
      return `${sourceName} ↔ ${targetName} (${bondLabel})`;
    }
    return bond?.public_status?.trim() || bond?.bond_type || entity.id.slice(0, 8);
  }

  const identity = entity.document.identity as { name?: string } | undefined;
  const plotLine = entity.document.plot_line as { title?: string } | undefined;
  return identity?.name ?? plotLine?.title ?? entity.id.slice(0, 8);
}

export function buildNpcDocument(input: {
  name: string;
  concept: string;
  publicDescription: string;
  secretLore: string;
  voiceAndTone: string;
  personalityTraits: string;
  factionId?: string | null;
  locationId?: string | null;
}): Record<string, unknown> {
  const traits = input.personalityTraits
    .split(",")
    .map((trait) => trait.trim())
    .filter(Boolean);

  return {
    metadata: { type: "NPC", system_agnostic: true, version: "2.0.0" },
    identity: {
      name: input.name.trim(),
      concept: input.concept.trim(),
      faction_id: normalizeEntityRefId(input.factionId) || null,
      current_location_id: normalizeEntityRefId(input.locationId) || null,
    },
    ai_narrative_profile: {
      public_description: input.publicDescription.trim(),
      secret_lore_master: input.secretLore.trim(),
      personality_traits: traits.length > 0 ? traits : ["misterioso"],
      voice_and_tone: input.voiceAndTone.trim() || "Neutral",
    },
    system_mechanics: {
      system_name: "agnóstico",
      power_scale: "medio",
      stats_summary: {},
      notable_features: [],
    },
    state_flags: {
      is_dead: false,
      is_present_in_scene: false,
      attitude_towards_party: "neutral",
      has_met_party: false,
      hidden_from_players: false,
    },
  };
}

export function buildLocationDocument(input: {
  name: string;
  locationType: string;
  publicDescription: string;
  secretLore: string;
  ambientTone: string;
}): Record<string, unknown> {
  return {
    metadata: { type: "LOCATION", version: "1.0.0" },
    identity: {
      name: input.name.trim(),
      location_type: input.locationType.trim() || "lugar",
      parent_location_id: null,
    },
    narrative_profile: {
      public_description: input.publicDescription.trim(),
      secret_lore_master: input.secretLore.trim(),
      ambient_tone: input.ambientTone.trim() || null,
      notable_features: [],
    },
    state_flags: {
      is_accessible_to_party: true,
      danger_level: 3,
      is_destroyed: false,
    },
  };
}

export function buildPcDocument(input: {
  name: string;
  concept: string;
  description: string;
  userId: string;
  factionId?: string | null;
  locationId?: string | null;
}): Record<string, unknown> {
  return {
    metadata: { type: "PC", system_agnostic: true, version: "2.0.0" },
    identity: {
      name: input.name.trim(),
      concept: input.concept.trim(),
      faction_id: normalizeEntityRefId(input.factionId) || null,
      current_location_id: normalizeEntityRefId(input.locationId) || null,
    },
    player_binding: {
      user_id: input.userId,
      is_active_in_campaign: true,
    },
    public_profile: {
      description: input.description.trim(),
      personality_traits: [],
    },
    system_mechanics: {
      system_name: "agnóstico",
      stats_summary: {},
      notable_features: [],
    },
    state_flags: {
      is_present_in_scene: false,
      is_incapacitated: false,
    },
  };
}

export function buildPcDocumentForGameSystem(input: {
  name: string;
  concept: string;
  description: string;
  userId: string;
  systemId: string;
  factionId?: string | null;
  locationId?: string | null;
}): Record<string, unknown> {
  return buildPcDocumentWithSheet({
    ...input,
    sheet: defaultSheetForGameSystem(input.systemId),
  });
}

export function buildFactionDocument(input: {
  name: string;
  factionType: string;
  publicDescription: string;
  secretLore: string;
  goals: string;
}): Record<string, unknown> {
  const goals = input.goals
    .split(",")
    .map((goal) => goal.trim())
    .filter(Boolean);

  return {
    metadata: { type: "FACTION", version: "1.0.0" },
    identity: {
      name: input.name.trim(),
      faction_type: input.factionType.trim() || "organización",
      headquarters_location_id: null,
    },
    narrative_profile: {
      public_description: input.publicDescription.trim(),
      secret_lore_master: input.secretLore.trim(),
      goals: goals.length > 0 ? goals : ["sobrevivir"],
    },
    state_flags: {
      attitude_towards_party: "neutral",
      influence_level: 5,
      is_active: true,
    },
  };
}

export function buildRelationshipDocument(input: {
  sourceId: string;
  targetId: string;
  bondType: string;
  publicStatus: string;
  secretNuance: string;
  tensionLevel: number;
}): Record<string, unknown> {
  const now = new Date().toISOString();
  return {
    metadata: { type: "RELATIONSHIP", created_at: now, last_updated: now },
    connection: {
      source_id: input.sourceId,
      target_id: input.targetId,
      is_bidirectional: true,
    },
    narrative_bond: {
      bond_type: input.bondType.trim() || "alianza",
      public_status: input.publicStatus.trim(),
      secret_nuance: input.secretNuance.trim(),
      tension_level: Math.min(10, Math.max(0, input.tensionLevel)),
    },
    ai_behavior_guidelines: {
      if_source_acts: "Considera el vínculo al narrar acciones del origen.",
      if_target_acts: "Considera el vínculo al narrar acciones del destino.",
    },
    state_flags: {
      is_secret_discovered_by_party: false,
      is_active: true,
    },
  };
}

export function buildArcManifestDocument(input?: {
  title?: string;
  globalSummary?: string;
  currentAct?: number;
  narrativeTone?: string;
}): Record<string, unknown> {
  return {
    metadata: { type: "ARC_MANIFEST" },
    plot_line: {
      title: input?.title?.trim() || "Arco principal",
      global_summary: input?.globalSummary?.trim() || "",
      current_act: input?.currentAct ?? 1,
      narrative_tone: input?.narrativeTone?.trim() || "Aventura",
    },
    active_quests: [],
    completed_milestones: [],
    state_flags: {
      is_main_plot_derailed: false,
      world_threat_level: 1,
    },
  };
}

export function newQuestId(): string {
  return crypto.randomUUID();
}
