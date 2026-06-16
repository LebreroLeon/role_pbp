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
  NPC: "NPC",
  PC: "Personaje jugador",
  FACTION: "Facción",
  LOCATION: "Ubicación",
  RELATIONSHIP: "Relación",
  ARC_MANIFEST: "Arco narrativo",
};

export const PLACEHOLDER_UUID = "00000000-0000-0000-0000-000000000001";

export function getEntityDisplayName(entity: CampaignEntity): string {
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
