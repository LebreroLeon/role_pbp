import type { CampaignEntity } from "../../api/types";
import { getEntityDisplayName } from "../entities/entityDefaults";

export type SpeakerType = "NARRATOR" | "MASTER" | "NPC" | "PC";

export type SpeakerOption = {
  id: string;
  label: string;
  speakerType: SpeakerType;
  entityType?: "NPC" | "PC";
};

export const DEFAULT_SPEAKER_OPTION_ID = "narrator";

export function buildSpeakerOptions(entities: CampaignEntity[] | undefined): SpeakerOption[] {
  const options: SpeakerOption[] = [
    {
      id: DEFAULT_SPEAKER_OPTION_ID,
      label: "Máster / Narrador",
      speakerType: "NARRATOR",
    },
  ];

  if (!entities?.length) return options;

  const npcs = entities
    .filter((entity) => entity.entity_type === "NPC")
    .sort((a, b) => getEntityDisplayName(a).localeCompare(getEntityDisplayName(b), "es"));
  const pcs = entities
    .filter((entity) => entity.entity_type === "PC")
    .sort((a, b) => getEntityDisplayName(a).localeCompare(getEntityDisplayName(b), "es"));

  for (const entity of npcs) {
    options.push({
      id: entity.id,
      label: getEntityDisplayName(entity),
      speakerType: "NPC",
      entityType: "NPC",
    });
  }

  for (const entity of pcs) {
    options.push({
      id: entity.id,
      label: getEntityDisplayName(entity),
      speakerType: "PC",
      entityType: "PC",
    });
  }

  return options;
}

export type SpeakerPayload = {
  speaker_type: SpeakerType;
  speaker_entity_id?: string;
  speaker_display_name: string;
};

export function speakerOptionToPayload(option: SpeakerOption): SpeakerPayload {
  return {
    speaker_type: option.speakerType,
    speaker_display_name: option.label,
    ...(option.speakerType === "NPC" || option.speakerType === "PC"
      ? { speaker_entity_id: option.id }
      : {}),
  };
}
