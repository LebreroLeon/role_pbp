import { defaultSheetForGameSystem } from "../character-sheet/pcDocument";
import { normalizeEntityRefId } from "./entityDefaults";

export function buildNpcDocumentForGameSystem(input: {
  name: string;
  concept: string;
  publicDescription: string;
  secretLore: string;
  voiceAndTone: string;
  personalityTraits: string;
  systemId: string;
  powerScale?: string;
  factionId?: string | null;
  locationId?: string | null;
}): Record<string, unknown> {
  const traits = input.personalityTraits
    .split(",")
    .map((trait) => trait.trim())
    .filter(Boolean);

  const hasMechanics = input.systemId !== "generic";

  return {
    metadata: {
      type: "NPC",
      system_agnostic: !hasMechanics,
      mechanics_enabled: hasMechanics,
      version: "2.0.0",
    },
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
    system_mechanics: hasMechanics
      ? {
          system_id: input.systemId,
          schema_version: "1.0.0",
          sheet: defaultSheetForGameSystem(input.systemId),
        }
      : {
          system_name: "agnóstico",
          power_scale: input.powerScale ?? "medium",
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

export function mergeNpcSheetIntoDocument(
  document: Record<string, unknown>,
  systemId: string,
  sheet: Record<string, unknown>,
): Record<string, unknown> {
  return {
    ...document,
    metadata: {
      ...(document.metadata as Record<string, unknown>),
      system_agnostic: false,
      mechanics_enabled: true,
    },
    system_mechanics: {
      system_id: systemId,
      schema_version: "1.0.0",
      sheet,
    },
  };
}

export function ensureNpcTypedMechanics(
  document: Record<string, unknown>,
  systemId: string,
): Record<string, unknown> {
  const mechanics = document.system_mechanics as Record<string, unknown> | undefined;
  if (mechanics && typeof mechanics.system_id === "string" && mechanics.sheet) {
    return document;
  }
  return mergeNpcSheetIntoDocument(document, systemId, defaultSheetForGameSystem(systemId) as Record<string, unknown>);
}
