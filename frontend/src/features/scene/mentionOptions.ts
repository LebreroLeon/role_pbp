import type { CampaignEntity } from "../../api/types";
import { enrichInitiativeEntry, buildSceneRoster, resolveSceneEntityDisplayName } from "../combat/sceneRoster";
import { matchesWorldViewFilter } from "../entities/compendiumTier";
import { getEntityDisplayName, isNpcWorldHidden } from "../entities/entityDefaults";
import { getCombatState, normalizeSceneState, type SceneStateInput } from "../scene/sceneState";

export type MentionOption = {
  id: string;
  label: string;
  entityType?: string;
  source: "scene" | "campaign";
};

export function buildMentionOptions(
  sceneState: SceneStateInput | null | undefined,
  entities: CampaignEntity[] | undefined,
  isMaster: boolean,
): MentionOption[] {
  const options: MentionOption[] = [];
  const seen = new Set<string>();

  function add(id: string, label: string, entityType?: string, source: MentionOption["source"] = "campaign") {
    if (!label.trim() || seen.has(id)) return;
    seen.add(id);
    options.push({ id, label, entityType, source });
  }

  if (isMaster) {
    if (sceneState) {
      const normalized = normalizeSceneState(sceneState);
      const combat = getCombatState(normalized);

      for (const entry of combat.initiative_order) {
        const enriched = enrichInitiativeEntry(entry, entities, sceneState, true);
        add(
          enriched.entity_id,
          enriched.display_name ?? enriched.entity_id.slice(0, 8),
          enriched.entity_type ?? undefined,
          "scene",
        );
      }

      for (const npcId of normalized.context.active_npc_ids) {
        const entity = entities?.find((item) => item.id === npcId);
        if (entity) {
          add(entity.id, getEntityDisplayName(entity), entity.entity_type, "scene");
        } else {
          add(npcId, npcId.slice(0, 8), "NPC", "scene");
        }
      }
    }

    if (entities) {
      for (const entity of entities) {
        if (entity.entity_type === "PC" || entity.entity_type === "NPC") {
          add(entity.id, getEntityDisplayName(entity), entity.entity_type, "campaign");
        }
      }
    }

    return options.sort((a, b) => a.label.localeCompare(b.label, "es"));
  }

  const roster = buildSceneRoster(sceneState, entities, false);
  for (const entry of roster) {
    add(entry.id, entry.label, entry.entityType, "scene");
  }

  if (entities) {
    for (const entity of entities) {
      if (seen.has(entity.id)) continue;
      if (entity.entity_type !== "PC" && entity.entity_type !== "NPC") continue;
      if (entity.entity_type === "NPC" && isNpcWorldHidden(entity)) continue;
      if (!matchesWorldViewFilter(entity, "story")) continue;
      const label = resolveSceneEntityDisplayName(entity, sceneState ?? {}, false);
      add(entity.id, label, entity.entity_type, "campaign");
    }
  }

  return options.sort((a, b) => a.label.localeCompare(b.label, "es"));
}

export function filterMentionOptions(options: MentionOption[], query: string): MentionOption[] {
  const normalized = query.trim().toLowerCase();
  if (!normalized) return options.slice(0, 8);

  return options
    .filter((option) => option.label.toLowerCase().includes(normalized))
    .slice(0, 8);
}
