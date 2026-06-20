import type { CharacterSheetUpsert } from "../../api/types";
import { normalizeEntityRefId } from "../entities/entityDefaults";
import type { CyberpunkRedSheet } from "./systems/cyberpunk_red/schema";
import { defaultCyberpunkRedSheet } from "./systems/cyberpunk_red/schema";
import type { Dnd5eSheet } from "./systems/dnd5e/schema";
import { defaultDnd5eSheet } from "./systems/dnd5e/schema";
import type { VtmV5Sheet } from "./systems/vtm_v5/schema";
import { defaultVtmV5Sheet } from "./systems/vtm_v5/schema";

export type GameSheet = Dnd5eSheet | CyberpunkRedSheet | VtmV5Sheet | Record<string, unknown>;

export function defaultSheetForGameSystem(systemId: string): GameSheet {
  switch (systemId) {
    case "dnd5e":
      return defaultDnd5eSheet();
    case "cyberpunk_red":
      return defaultCyberpunkRedSheet();
    case "vtm_v5":
      return defaultVtmV5Sheet();
    default:
      return {};
  }
}

export function buildPcDocumentWithSheet(input: {
  name: string;
  concept: string;
  description: string;
  userId: string;
  systemId: string;
  sheet?: GameSheet;
  factionId?: string | null;
  locationId?: string | null;
}): Record<string, unknown> {
  const sheet = input.sheet ?? defaultSheetForGameSystem(input.systemId);

  return {
    metadata: {
      type: "PC",
      system_agnostic: false,
      mechanics_enabled: true,
      version: "2.0.0",
    },
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
      system_id: input.systemId,
      schema_version: "1.0.0",
      sheet,
    },
    state_flags: {
      is_present_in_scene: false,
      is_incapacitated: false,
    },
  };
}

export function extractSheetFromEntity(
  document: Record<string, unknown>,
): { systemId: string; sheet: unknown } | null {
  const mechanics = document.system_mechanics as
    | { system_id?: string; sheet?: unknown; stats_summary?: unknown }
    | undefined;

  if (!mechanics) return null;

  if (mechanics.system_id && mechanics.sheet) {
    return { systemId: mechanics.system_id, sheet: mechanics.sheet };
  }

  return null;
}

export function buildCharacterSheetUpsert(input: {
  name: string;
  concept: string;
  description: string;
  systemId: string;
  sheet?: GameSheet;
  factionId?: string | null;
  locationId?: string | null;
}): CharacterSheetUpsert {
  const sheet = input.sheet ?? defaultSheetForGameSystem(input.systemId);

  return {
    identity: {
      name: input.name.trim(),
      concept: input.concept.trim(),
      faction_id: normalizeEntityRefId(input.factionId) || null,
      current_location_id: normalizeEntityRefId(input.locationId) || null,
    },
    public_profile: {
      description: input.description.trim(),
      personality_traits: [],
    },
    system_mechanics: {
      system_id: input.systemId,
      schema_version: "1.0.0",
      sheet,
    },
    state_flags: {
      is_present_in_scene: false,
      is_incapacitated: false,
    },
  };
}

export function documentToCharacterSheetUpsert(document: Record<string, unknown>): CharacterSheetUpsert {
  const identity = document.identity as {
    name?: string;
    concept?: string;
    faction_id?: string | null;
    current_location_id?: string;
  };
  const publicProfile = document.public_profile as
    | { description?: string; personality_traits?: string[] }
    | undefined;
  const mechanics = document.system_mechanics as
    | { system_id?: string; schema_version?: string; sheet?: Record<string, unknown> }
    | undefined;
  const stateFlags = document.state_flags as
    | { is_present_in_scene?: boolean; is_incapacitated?: boolean }
    | undefined;

  return {
    identity: {
      name: identity?.name ?? "",
      concept: identity?.concept ?? "",
      faction_id: identity?.faction_id ?? null,
      current_location_id: normalizeEntityRefId(identity?.current_location_id) || null,
    },
    public_profile: publicProfile
      ? {
          description: publicProfile.description ?? "",
          personality_traits: publicProfile.personality_traits ?? [],
        }
      : null,
    system_mechanics: {
      system_id: mechanics?.system_id ?? "generic",
      schema_version: mechanics?.schema_version ?? "1.0.0",
      sheet: mechanics?.sheet ?? {},
    },
    state_flags: stateFlags
      ? {
          is_present_in_scene: stateFlags.is_present_in_scene ?? false,
          is_incapacitated: stateFlags.is_incapacitated ?? false,
        }
      : null,
  };
}

export function mergeSheetIntoDocument(
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
