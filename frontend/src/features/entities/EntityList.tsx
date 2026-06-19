import type { CampaignEntity, EntityType } from "./entityDefaults";
import { ENTITY_TYPE_LABELS, getEntityDisplayName } from "./entityDefaults";
import { Button } from "../../components/ui";

type EntityListProps = {
  entities: CampaignEntity[];
  isMaster: boolean;
  onEdit?: (entity: CampaignEntity) => void;
  editingId?: string | null;
  onDelete?: (entityId: string) => void;
  deletingId?: string | null;
};

export function EntityList({ entities, isMaster, onEdit, editingId, onDelete, deletingId }: EntityListProps) {
  if (entities.length === 0) {
    return <p className="muted">El mundo está vacío. Crea o importa NPCs y ubicaciones.</p>;
  }

  const grouped = entities.reduce<Record<EntityType, CampaignEntity[]>>(
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
            {items.map((entity) => (
              <li key={entity.id} className={`entity-card ${editingId === entity.id ? "is-editing" : ""}`}>
                <div>
                  <strong>{getEntityDisplayName(entity, entities)}</strong>
                  <p className="muted entity-summary">{summarizeEntity(entity)}</p>
                </div>
                {isMaster && (
                  <div className="entity-card__actions">
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
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}

function isWorldEntity(entityType: EntityType): boolean {
  return entityType === "LOCATION" || entityType === "FACTION" || entityType === "RELATIONSHIP";
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
  const identity = entity.document.identity as { concept?: string } | undefined;
  return identity?.concept?.slice(0, 120) ?? "";
}
