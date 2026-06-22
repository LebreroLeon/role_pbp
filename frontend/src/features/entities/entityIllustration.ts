import type { ChatMessage } from "../../api/types";
import type { CampaignEntity } from "./entityDefaults";
import { getNpcPlayerVisibility } from "./playerVisibility";

export function extractIllustrationUrl(entity: CampaignEntity): string | undefined {
  const document = entity.document;
  if (entity.entity_type === "PC") {
    const profile = document.public_profile as { illustration_url?: string } | undefined;
    return profile?.illustration_url?.trim() || undefined;
  }
  if (entity.entity_type === "NPC") {
    const profile = document.ai_narrative_profile as { illustration_url?: string } | undefined;
    return profile?.illustration_url?.trim() || undefined;
  }
  if (entity.entity_type === "LOCATION" || entity.entity_type === "FACTION") {
    const profile = document.narrative_profile as { illustration_url?: string } | undefined;
    return profile?.illustration_url?.trim() || undefined;
  }
  if (entity.entity_type === "RELATIONSHIP") {
    const bond = document.narrative_bond as { illustration_url?: string } | undefined;
    return bond?.illustration_url?.trim() || undefined;
  }
  return undefined;
}

export function isExternalIllustrationUrl(url: string): boolean {
  return /^https?:\/\//i.test(url);
}

export function entityIllustrationDownloadPath(entityId: string): string {
  return `/api/v1/entities/${entityId}/illustration`;
}

export function canPlayerSeeIllustration(entity: CampaignEntity): boolean {
  if (entity.entity_type === "NPC") {
    return getNpcPlayerVisibility(entity) === "visible";
  }
  return (
    entity.entity_type === "PC" ||
    entity.entity_type === "LOCATION" ||
    entity.entity_type === "FACTION" ||
    entity.entity_type === "RELATIONSHIP"
  );
}

export function canShowIllustrationPreview(entity: CampaignEntity, isMaster: boolean): boolean {
  if (!extractIllustrationUrl(entity)) return false;
  if (isMaster) return true;
  return canPlayerSeeIllustration(entity);
}

export function resolveMessageSpeakerEntity(
  message: ChatMessage,
  entities?: CampaignEntity[],
): CampaignEntity | undefined {
  if (!entities?.length) return undefined;

  const entityId = message.speaker_entity_id ?? message.entity_id;
  if (!entityId) return undefined;

  return entities.find((item) => item.id === entityId);
}
