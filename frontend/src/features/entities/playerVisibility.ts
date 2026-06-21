import type { CampaignEntity } from "./entityDefaults";

export type NpcPlayerVisibility = "hidden" | "unknown" | "visible";

export const NPC_VISIBILITY_LABELS: Record<NpcPlayerVisibility, string> = {
  hidden: "Oculto",
  unknown: "Desconocido",
  visible: "Visible",
};

export function getNpcPlayerVisibility(entity: CampaignEntity): NpcPlayerVisibility {
  if (entity.entity_type !== "NPC") return "visible";
  const flags = entity.document.state_flags as
    | { player_visibility?: string; hidden_from_players?: boolean }
    | undefined;
  const visibility = flags?.player_visibility;
  if (visibility === "hidden" || visibility === "unknown" || visibility === "visible") {
    return visibility;
  }
  if (flags?.hidden_from_players) return "hidden";
  return "visible";
}

export function isNpcWorldHidden(entity: CampaignEntity): boolean {
  return getNpcPlayerVisibility(entity) === "hidden";
}

export function isNpcMaskedForPlayer(entity: CampaignEntity): boolean {
  return getNpcPlayerVisibility(entity) === "unknown";
}

export function withNpcPlayerVisibility(
  document: Record<string, unknown>,
  visibility: NpcPlayerVisibility,
): Record<string, unknown> {
  const flags = {
    ...(document.state_flags as Record<string, unknown>),
    player_visibility: visibility,
    hidden_from_players: visibility === "hidden",
  };
  return { ...document, state_flags: flags };
}

export const NPC_VISIBILITY_OPTIONS: NpcPlayerVisibility[] = ["hidden", "unknown", "visible"];
