import type { CampaignEntity, EntityType } from "./entityDefaults";
import {
  ENTITY_TYPE_LABELS,
  getEntityDisplayName,
  getNpcPlayerVisibility,
  isNpcWorldHidden,
  withNpcPlayerVisibility,
  type NpcPlayerVisibility,
} from "./entityDefaults";
import { NpcVisibilityControl } from "./NpcVisibilityControl";
import { Button } from "../../components/ui";
import { useUpdateEntityMutation } from "../../hooks/mutations/useEntityMutations";

type EntityListProps = {
  campaignId: string;
  entities: CampaignEntity[];
  isMaster: boolean;
  onEdit?: (entity: CampaignEntity) => void;
  editingId?: string | null;
  onDelete?: (entityId: string) => void;
  deletingId?: string | null;
};

export function EntityList({
  campaignId,
  entities,
  isMaster,
  onEdit,
  editingId,
  onDelete,
  deletingId,
}: EntityListProps) {
  const updateMutation = useUpdateEntityMutation(campaignId);

  const visibleEntities = isMaster
    ? entities
    : entities.filter((entity) => !(entity.entity_type === "NPC" && isNpcWorldHidden(entity)));

  if (visibleEntities.length === 0) {
    return <p className="muted">El mundo está vacío. Crea o importa NPCs y ubicaciones.</p>;
  }

  async function handleNpcVisibilityChange(entity: CampaignEntity, visibility: NpcPlayerVisibility) {
    await updateMutation.mutateAsync({
      entityId: entity.id,
      document: withNpcPlayerVisibility(entity.document, visibility),
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

  return (
    <div className="entity-groups">
      {Object.entries(grouped).map(([type, items]) => (
        <section key={type} className="entity-group">
          <h3>{ENTITY_TYPE_LABELS[type as EntityType]}</h3>
          <ul className="entity-list">
            {items.map((entity) => {
              const npcVisibility =
                entity.entity_type === "NPC" ? getNpcPlayerVisibility(entity) : null;

              const summary = summarizeEntity(entity);

              return (
                <li key={entity.id} className={`entity-card ${editingId === entity.id ? "is-editing" : ""}`}>
                  <div className="entity-card__main">
                    <div className="entity-card__header">
                      <span className="entity-card__name">{getEntityDisplayName(entity, entities)}</span>
                      {isMaster && (
                        <div className="entity-card__actions">
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
      ))}
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
