import type { CampaignEntity } from "../entities/entityDefaults";
import { normalizeEntityRefId } from "../entities/entityDefaults";

export function readSaveWarnings(saved: CampaignEntity): string | null {
  if (!saved.warnings?.length) return null;
  return saved.warnings.join(" ");
}

export function clearedLocationIdFromSave(saved: CampaignEntity): boolean {
  const identity = saved.document.identity as { current_location_id?: string | null } | undefined;
  return !normalizeEntityRefId(identity?.current_location_id);
}
