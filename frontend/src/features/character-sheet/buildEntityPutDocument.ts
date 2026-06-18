import {
  defaultSheetForGameSystem,
  documentToCharacterSheetUpsert,
  extractSheetFromEntity,
  mergeSheetIntoDocument,
  type GameSheet,
} from "./pcDocument";
import { mergeNpcSheetIntoDocument } from "../entities/npcDocument";
import type { CampaignEntity } from "../entities/entityDefaults";

type NarrativeFields = {
  name: string;
  concept: string;
  publicDescription: string;
  secretLore?: string;
  voiceAndTone?: string;
  personalityTraits?: string[];
};

function buildNpcPutDocument(
  workingDocument: Record<string, unknown>,
  narrative: NarrativeFields,
): Record<string, unknown> {
  const traits =
    narrative.personalityTraits && narrative.personalityTraits.length > 0
      ? narrative.personalityTraits
      : ["misterioso"];

  return {
    ...workingDocument,
    identity: {
      ...(workingDocument.identity as Record<string, unknown>),
      name: narrative.name.trim(),
      concept: narrative.concept.trim(),
    },
    ai_narrative_profile: {
      ...(workingDocument.ai_narrative_profile as Record<string, unknown>),
      public_description: narrative.publicDescription.trim(),
      secret_lore_master: narrative.secretLore?.trim() ?? "",
      voice_and_tone: narrative.voiceAndTone?.trim() || "Neutral",
      personality_traits: traits,
    },
  };
}

function buildPcPutDocument(
  workingDocument: Record<string, unknown>,
  narrative: NarrativeFields,
  gameSystem: string,
  sheet?: GameSheet,
): Record<string, unknown> {
  let doc: Record<string, unknown> = {
    ...workingDocument,
    identity: {
      ...(workingDocument.identity as Record<string, unknown>),
      name: narrative.name.trim(),
      concept: narrative.concept.trim(),
    },
    public_profile: {
      ...((workingDocument.public_profile as Record<string, unknown> | undefined) ?? {}),
      description: narrative.publicDescription.trim(),
      personality_traits:
        (workingDocument.public_profile as { personality_traits?: string[] } | undefined)?.personality_traits ?? [],
    },
  };

  if (sheet) {
    doc = mergeSheetIntoDocument(doc, gameSystem, sheet as Record<string, unknown>);
  }

  const upsert = documentToCharacterSheetUpsert(doc);
  const metadata = workingDocument.metadata as Record<string, unknown> | undefined;
  const existingFlags = workingDocument.state_flags as
    | { is_present_in_scene?: boolean; is_incapacitated?: boolean }
    | undefined;

  return {
    metadata: {
      type: "PC",
      system_agnostic: false,
      mechanics_enabled: true,
      version: metadata?.version ?? "2.0.0",
    },
    identity: upsert.identity,
    player_binding: workingDocument.player_binding,
    public_profile: upsert.public_profile,
    system_mechanics: upsert.system_mechanics,
    state_flags: upsert.state_flags ?? {
      is_present_in_scene: existingFlags?.is_present_in_scene ?? false,
      is_incapacitated: existingFlags?.is_incapacitated ?? false,
    },
  };
}

export function buildEntityPutDocument(input: {
  entity: CampaignEntity;
  workingDocument: Record<string, unknown>;
  gameSystem: string;
  narrative: NarrativeFields;
  sheet?: GameSheet;
}): Record<string, unknown> {
  const { entity, workingDocument, gameSystem, narrative, sheet } = input;

  if (entity.entity_type === "PC") {
    return buildPcPutDocument(workingDocument, narrative, gameSystem, sheet);
  }

  let document = buildNpcPutDocument(workingDocument, narrative);
  if (sheet) {
    document = mergeNpcSheetIntoDocument(document, gameSystem, sheet as Record<string, unknown>);
  } else if (gameSystem !== "generic") {
    const extracted = extractSheetFromEntity(document);
    if (!extracted?.sheet) {
      document = mergeNpcSheetIntoDocument(
        document,
        gameSystem,
        defaultSheetForGameSystem(gameSystem) as Record<string, unknown>,
      );
    }
  }
  return document;
}
