import type { CampaignEntity } from "./entityDefaults";
import { getEntityDisplayName } from "./entityDefaults";
import { isNpcMaskedForPlayer } from "./playerVisibility";
import { HIDDEN_NPC_LABEL } from "../combat/sceneRoster";
import { canPlayerSeeIllustration, extractIllustrationUrl } from "./entityIllustration";

export function resolvePublicDisplayName(
  entity: CampaignEntity,
  entities: CampaignEntity[],
  isMaster: boolean,
): string {
  if (!isMaster && entity.entity_type === "NPC" && isNpcMaskedForPlayer(entity)) {
    return HIDDEN_NPC_LABEL;
  }
  return getEntityDisplayName(entity, entities);
}

export function extractPublicDescription(entity: CampaignEntity, isMaster: boolean): string {
  if (!isMaster && entity.entity_type === "NPC" && isNpcMaskedForPlayer(entity)) {
    return "";
  }

  if (entity.entity_type === "NPC") {
    const profile = entity.document.ai_narrative_profile as { public_description?: string } | undefined;
    return profile?.public_description?.trim() ?? "";
  }
  if (entity.entity_type === "LOCATION" || entity.entity_type === "FACTION") {
    const profile = entity.document.narrative_profile as { public_description?: string } | undefined;
    return profile?.public_description?.trim() ?? "";
  }
  if (entity.entity_type === "RELATIONSHIP") {
    const bond = entity.document.narrative_bond as { public_status?: string } | undefined;
    return bond?.public_status?.trim() ?? "";
  }
  if (entity.entity_type === "PC") {
    const profile = entity.document.public_profile as { description?: string } | undefined;
    return profile?.description?.trim() ?? "";
  }

  return "";
}

export function resolvePublicIllustrationUrl(entity: CampaignEntity, isMaster: boolean): string | undefined {
  const url = extractIllustrationUrl(entity);
  if (!url) return undefined;
  if (isMaster) return url;
  return canPlayerSeeIllustration(entity) ? url : undefined;
}
