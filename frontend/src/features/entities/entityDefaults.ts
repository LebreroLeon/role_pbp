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
      faction_id: PLACEHOLDER_UUID,
      current_location_id: PLACEHOLDER_UUID,
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
}): Record<string, unknown> {
  return {
    metadata: { type: "PC", system_agnostic: true, version: "2.0.0" },
    identity: {
      name: input.name.trim(),
      concept: input.concept.trim(),
      faction_id: null,
      current_location_id: PLACEHOLDER_UUID,
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
