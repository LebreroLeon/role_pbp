import type { CampaignEntity } from "../../api/types";

export function entityLabel(entity: CampaignEntity): string {
  const identity = entity.document.identity as { name?: string } | undefined;
  if (identity?.name?.trim()) return identity.name.trim();
  return entity.id.slice(0, 8);
}
