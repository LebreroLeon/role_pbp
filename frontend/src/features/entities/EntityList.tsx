import type { CampaignEntity, EntityType } from "./entityDefaults";
import {
  ENTITY_TYPE_LABELS,
  getEntityDisplayName,
  getNpcPlayerVisibility,
  isNpcWorldHidden,
  withNpcPlayerVisibility,
  type NpcPlayerVisibility,
} from "./entityDefaults";
import {
  COMPENDIUM_TIER_LABELS,
  getNpcCompendiumTier,
  matchesWorldViewFilter,
  withNpcCompendiumTier,
  type CompendiumTier,
  type WorldViewFilter,
} from "./compendiumTier";
import { NpcVisibilityControl } from "./NpcVisibilityControl";
import { Button } from "../../components/ui";
import { useUpdateEntityMutation } from "../../hooks/mutations/useEntityMutations";

type EntityListProps = {
  campaignId: string;
  entities: CampaignEntity[];
  isMaster: boolean;
  viewFilter?: WorldViewFilter;
  onEdit?: (entity: CampaignEntity) => void;
  editingId?: string | null;
  onDelete?: (entityId: string) => void;
  deletingId?: string | null;
  emptyMessage?: string;
};

export function EntityList({
  campaignId,
  entities,
  isMaster,
  viewFilter = "all",
  onEdit,
  editingId,
  onDelete,
  deletingId,
  emptyMessage,
}: EntityListProps) {
  const updateMutation = useUpdateEntityMutation(campaignId);

  const visibleEntities = (isMaster ? entities : entities.filter((entity) => !(entity.entity_type === "NPC" && isNpcWorldHidden(entity))))
    .filter((entity) => entity.entity_type !== "ARC_MANIFEST")
    .filter((entity) => matchesWorldViewFilter(entity, isMaster ? viewFilter : "story"));

  if (visibleEntities.length === 0) {
    return (
      <p className="muted">
        {emptyMessage ??
          (viewFilter === "combat"
            ? "Sin entidades de combate. Invoca monstruos del catálogo SRD."
            : viewFilter === "story"
              ? "Sin entidades narrativas. Añade NPCs, ubicaciones o facciones relevantes."
              : "El mundo está vacío. Crea o importa entidades.")}
      </p>
    );
  }

  async function handleNpcVisibilityChange(entity: CampaignEntity, visibility: NpcPlayerVisibility) {
    await updateMutation.mutateAsync({
      entityId: entity.id,
      document: withNpcPlayerVisibility(entity.document, visibility),
    });
  }

  async function handleCompendiumTierChange(entity: CampaignEntity, tier: CompendiumTier) {
    await updateMutation.mutateAsync({
      entityId: entity.id,
      document: withNpcCompendiumTier(entity.document, tier),
    });
  }

  const grouped = visibleEntities.reduce<Record<EntityType, CampaignEntity[]>>(
    (acc, entity) => {
      acc[entity.entity_type] = acc[entity.entity_type] ?? [];
      acc[entity.entity_type].push(entity);
      return acc;
    },
    {} as Record<EntityType, CampaignEntity[]>,
  );

  const typeOrder: EntityType[] = ["NPC", "LOCATION", "FACTION", "RELATIONSHIP", "PC"];
  const sortedTypes = typeOrder.filter((type) => grouped[type]?.length);

  return (
    <div className="entity-groups">
      {sortedTypes.map((type) => {
        const items = grouped[type];
        return (
          <section key={type} className="entity-group">
            <h3>{ENTITY_TYPE_LABELS[type]}</h3>
            <ul className="entity-list">
              {items.map((entity) => {
                const npcVisibility = entity.entity_type === "NPC" ? getNpcPlayerVisibility(entity) : null;
                const compendiumTier = entity.entity_type === "NPC" ? getNpcCompendiumTier(entity) : null;
                const summary = summarizeEntity(entity);

                return (
                  <li key={entity.id} className={`entity-card ${editingId === entity.id ? "is-editing" : ""}`}>
                    <div className="entity-card__main">
                      <div className="entity-card__header">
                        <span className="entity-card__name">{getEntityDisplayName(entity, entities)}</span>
                        {isMaster && (
                          <div className="entity-card__actions">
                            {entity.entity_type === "NPC" && compendiumTier && (
                              <label className="entity-card__tier">
                                <span className="sr-only">Clasificación compendio</span>
                                <select
                                  value={compendiumTier}
                                  onChange={(event) => {
                                    void handleCompendiumTierChange(entity, event.target.value as CompendiumTier);
                                  }}
                                  disabled={updateMutation.isPending}
                                  aria-label={`Clasificación de ${getEntityDisplayName(entity, entities)}`}
                                >
                                  {(Object.keys(COMPENDIUM_TIER_LABELS) as CompendiumTier[]).map((tier) => (
                                    <option key={tier} value={tier}>
                                      {COMPENDIUM_TIER_LABELS[tier]}
                                    </option>
                                  ))}
                                </select>
                              </label>
                            )}
                            {entity.entity_type === "NPC" && npcVisibility && (
                              <NpcVisibilityControl
                                value={npcVisibility}
                                onChange={(visibility) => {
                                  void handleNpcVisibilityChange(entity, visibility);
                                }}
                                disabled={updateMutation.isPending}
                                compact
                                className="entity-card__visibility"
                              />
                            )}
                            {onEdit && (entity.entity_type === "NPC" || isWorldEntity(entity.entity_type)) && (
                              <Button className="secondary" onClick={() => onEdit(entity)}>
                                {editingId === entity.id ? "Editando" : editLabel(entity.entity_type)}
                              </Button>
                            )}
                            {onDelete && (
                              <Button
                                className="secondary"
                                disabled={deletingId === entity.id}
                                onClick={() => onDelete(entity.id)}
                              >
                                {deletingId === entity.id ? "..." : "Eliminar"}
                              </Button>
                            )}
                          </div>
                        )}
                      </div>
                      {summary && <p className="muted entity-summary">{summary}</p>}
                    </div>
                  </li>
                );
              })}
            </ul>
          </section>
        );
      })}
    </div>
  );
}

function isWorldEntity(entityType: EntityType): boolean {
  return (
    entityType === "LOCATION" ||
    entityType === "FACTION" ||
    entityType === "RELATIONSHIP" ||
    entityType === "ARC_MANIFEST"
  );
}

function editLabel(entityType: EntityType): string {
  if (entityType === "NPC") return "Editar ficha";
  return "Editar";
}

function summarizeEntity(entity: CampaignEntity): string {
  if (entity.entity_type === "NPC") {
    const profile = entity.document.ai_narrative_profile as { public_description?: string } | undefined;
    return profile?.public_description?.slice(0, 120) ?? "";
  }
  if (entity.entity_type === "LOCATION") {
    const profile = entity.document.narrative_profile as { public_description?: string } | undefined;
    return profile?.public_description?.slice(0, 120) ?? "";
  }
  if (entity.entity_type === "FACTION") {
    const profile = entity.document.narrative_profile as { public_description?: string } | undefined;
    return profile?.public_description?.slice(0, 120) ?? "";
  }
  if (entity.entity_type === "RELATIONSHIP") {
    const bond = entity.document.narrative_bond as { public_status?: string } | undefined;
    return bond?.public_status?.slice(0, 120) ?? "";
  }
  if (entity.entity_type === "PC") {
    const profile = entity.document.public_profile as { description?: string } | undefined;
    return profile?.description?.slice(0, 120) ?? "";
  }
  if (entity.entity_type === "ARC_MANIFEST") {
    const plotLine = entity.document.plot_line as { global_summary?: string; title?: string } | undefined;
    return plotLine?.global_summary?.slice(0, 120) ?? plotLine?.title ?? "";
  }
  const identity = entity.document.identity as { concept?: string } | undefined;
  return identity?.concept?.slice(0, 120) ?? "";
}
