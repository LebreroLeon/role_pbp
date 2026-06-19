import type { CampaignEntity, ChatMessage } from "../../api/types";

export function extractAvatarUrl(entity: CampaignEntity): string | undefined {
  const document = entity.document;
  if (entity.entity_type === "PC") {
    const profile = document.public_profile as { avatar_url?: string } | undefined;
    return profile?.avatar_url?.trim() || undefined;
  }
  if (entity.entity_type === "NPC") {
    const profile = document.ai_narrative_profile as { avatar_url?: string } | undefined;
    return profile?.avatar_url?.trim() || undefined;
  }
  return undefined;
}

export function resolveMessageAvatarUrl(
  message: ChatMessage,
  entities?: CampaignEntity[],
): string | undefined {
  if (!entities?.length) return undefined;

  const entityId = message.speaker_entity_id ?? message.entity_id;
  if (!entityId) return undefined;

  const entity = entities.find((item) => item.id === entityId);
  if (!entity) return undefined;

  return extractAvatarUrl(entity);
}

export function resolveEntityAvatarUrl(
  entityId: string | undefined,
  entities?: CampaignEntity[],
): string | undefined {
  if (!entityId || !entities?.length) return undefined;
  const entity = entities.find((item) => item.id === entityId);
  if (!entity) return undefined;
  return extractAvatarUrl(entity);
}

export function isExternalAvatarUrl(url: string): boolean {
  return /^https?:\/\//i.test(url);
}

export function entityAvatarDownloadPath(entityId: string): string {
  return `/api/v1/entities/${entityId}/avatar`;
}
