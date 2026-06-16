import type { CampaignEntity, EntityType } from "./entityDefaults";
import { ENTITY_TYPE_LABELS, getEntityDisplayName } from "./entityDefaults";
import { Button } from "../../components/ui";

type EntityListProps = {
  entities: CampaignEntity[];
  isMaster: boolean;
  onDelete?: (entityId: string) => void;
  deletingId?: string | null;
};

export function EntityList({ entities, isMaster, onDelete, deletingId }: EntityListProps) {
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
              <li key={entity.id} className="entity-card">
                <div>
                  <strong>{getEntityDisplayName(entity)}</strong>
                  <p className="muted entity-summary">{summarizeEntity(entity)}</p>
                </div>
                {isMaster && onDelete && (
                  <Button
                    className="secondary"
                    disabled={deletingId === entity.id}
                    onClick={() => onDelete(entity.id)}
                  >
                    {deletingId === entity.id ? "..." : "Eliminar"}
                  </Button>
                )}
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
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
  if (entity.entity_type === "PC") {
    const profile = entity.document.public_profile as { description?: string } | undefined;
    return profile?.description?.slice(0, 120) ?? "";
  }
  const identity = entity.document.identity as { concept?: string } | undefined;
  return identity?.concept?.slice(0, 120) ?? "";
}
