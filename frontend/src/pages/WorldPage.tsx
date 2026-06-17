import { useState } from "react";
import { useParams } from "react-router-dom";

import { SECTION_ICONS } from "../components/icons";
import { Panel, PanelHeader } from "../components/ui";
import { EntitySheetEditor } from "../features/character-sheet/EntitySheetEditor";
import { CreateEntityForm, EntityList, ImportExportPanel } from "../features/entities";
import { useDeleteEntityMutation } from "../hooks/mutations/useEntityMutations";
import { useCampaignMembersQuery, useCampaignQuery } from "../hooks/queries/useCampaignQueries";
import { useEntitiesQuery } from "../hooks/queries/useEntityQueries";

export function WorldPage() {
  const { campaignId = "" } = useParams();
  const { data: campaign } = useCampaignQuery(campaignId);
  const { data: members = [] } = useCampaignMembersQuery(campaignId);
  const { data: entities = [] } = useEntitiesQuery(campaignId);
  const deleteMutation = useDeleteEntityMutation(campaignId);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [editingEntityId, setEditingEntityId] = useState<string | null>(null);

  const isMaster = campaign?.role === "MASTER";
  const gameSystem = campaign?.game_system ?? "generic";
  const editingEntity = editingEntityId ? entities.find((entity) => entity.id === editingEntityId) ?? null : null;

  async function handleDelete(entityId: string) {
    setDeletingId(entityId);
    try {
      await deleteMutation.mutateAsync(entityId);
      if (editingEntityId === entityId) {
        setEditingEntityId(null);
      }
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="world-page">
      <Panel>
        <PanelHeader
          icon={SECTION_ICONS.mundo}
          iconTone="violet"
          title="Mundo"
          description={
            isMaster
              ? "NPCs y ubicaciones de la campaña. Edita fichas mecánicas y lore secreto aquí; los jugadores solo ven lo público."
              : "Personajes y lugares que tu PJ conoce. Los secretos del Máster no se muestran aquí."
          }
        />
        <EntityList
          entities={entities}
          isMaster={Boolean(isMaster)}
          onEdit={isMaster ? (entity) => setEditingEntityId(entity.id) : undefined}
          editingId={editingEntityId}
          onDelete={isMaster ? handleDelete : undefined}
          deletingId={deletingId}
        />
      </Panel>

      {isMaster && editingEntity?.entity_type === "NPC" && (
        <Panel className="world-page__editor">
          <PanelHeader
            icon={SECTION_ICONS.mundo}
            iconTone="teal"
            title={`Editar NPC — ${(editingEntity.document.identity as { name?: string })?.name ?? "Sin nombre"}`}
            description="Ficha narrativa + mecánica completa. Los jugadores no ven secret_lore_master ni stats ocultos."
          />
          <EntitySheetEditor
            campaignId={campaignId}
            entity={editingEntity}
            gameSystem={gameSystem}
            onSaved={() => setEditingEntityId(null)}
            onCancel={() => setEditingEntityId(null)}
          />
        </Panel>
      )}

      {isMaster && (
        <>
          <CreateEntityForm
            campaignId={campaignId}
            members={members}
            gameSystem={gameSystem}
            onNpcCreated={(entity) => setEditingEntityId(entity.id)}
          />
          <ImportExportPanel campaignId={campaignId} />
        </>
      )}
    </div>
  );
}
