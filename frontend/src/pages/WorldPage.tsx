import { useState } from "react";
import { useParams } from "react-router-dom";

import { SECTION_ICONS } from "../components/icons";
import { Panel, PanelHeader, SlideOver, Toast } from "../components/ui";
import { EntitySheetEditor } from "../features/character-sheet/EntitySheetEditor";
import { CreateEntityForm, EntityList, ImportExportPanel, WorldEntityEditor } from "../features/entities";
import { ENTITY_TYPE_LABELS, getEntityDisplayName } from "../features/entities/entityDefaults";
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
  const [editorMode, setEditorMode] = useState<"create" | "edit">("edit");
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const isMaster = campaign?.role === "MASTER";
  const gameSystem = campaign?.game_system ?? "generic";
  const editingEntity = editingEntityId ? entities.find((entity) => entity.id === editingEntityId) ?? null : null;

  function openEditor(entityId: string, mode: "create" | "edit" = "edit") {
    setEditorMode(mode);
    setEditingEntityId(entityId);
  }

  function closeEditor() {
    setEditingEntityId(null);
    setEditorMode("edit");
  }

  async function handleDelete(entityId: string) {
    setDeletingId(entityId);
    try {
      await deleteMutation.mutateAsync(entityId);
      if (editingEntityId === entityId) {
        closeEditor();
      }
    } finally {
      setDeletingId(null);
    }
  }

  function handleSaved() {
    closeEditor();
    const label = editingEntity ? ENTITY_TYPE_LABELS[editingEntity.entity_type] : "Entidad";
    setToastMessage(
      editorMode === "create"
        ? `${label} creado y guardado correctamente.`
        : `${label} actualizado correctamente.`,
    );
  }

  const isWorldEntity =
    editingEntity?.entity_type === "LOCATION" ||
    editingEntity?.entity_type === "FACTION" ||
    editingEntity?.entity_type === "RELATIONSHIP";

  const editorTitle = editingEntity
    ? editingEntity.entity_type === "NPC"
      ? editorMode === "create"
        ? `Nuevo NPC — ${(editingEntity.document.identity as { name?: string })?.name ?? "Sin nombre"}`
        : `Editar NPC — ${(editingEntity.document.identity as { name?: string })?.name ?? "Sin nombre"}`
      : `Editar ${ENTITY_TYPE_LABELS[editingEntity.entity_type]} — ${getEntityDisplayName(editingEntity, entities)}`
    : "";

  return (
    <div className="world-page">
      <Toast message={toastMessage} onDismiss={() => setToastMessage(null)} />

      <Panel>
        <PanelHeader
          icon={SECTION_ICONS.mundo}
          iconTone="violet"
          title="Mundo"
          description={
            isMaster
              ? "NPCs, ubicaciones, facciones y relaciones. Edita lore y fichas aquí; los jugadores solo ven lo público."
              : "Personajes y lugares que tu PJ conoce. Los secretos del Máster no se muestran aquí."
          }
        />
        <EntityList
          entities={entities}
          isMaster={Boolean(isMaster)}
          onEdit={isMaster ? (entity) => openEditor(entity.id, "edit") : undefined}
          editingId={editingEntityId}
          onDelete={isMaster ? handleDelete : undefined}
          deletingId={deletingId}
        />
      </Panel>

      {isMaster && editingEntity?.entity_type === "NPC" && (
        <SlideOver
          open
          title={editorTitle}
          description={
            editorMode === "create"
              ? "Completa la ficha del NPC recién creado. Los jugadores no ven secret_lore_master ni stats ocultos."
              : "Ficha narrativa + mecánica completa. Los jugadores no ven secret_lore_master ni stats ocultos."
          }
          onClose={closeEditor}
        >
          <EntitySheetEditor
            key={`${editingEntity.id}-${editingEntity.updated_at}`}
            campaignId={campaignId}
            entity={editingEntity}
            gameSystem={gameSystem}
            mode={editorMode}
            onSaved={handleSaved}
            onCancel={closeEditor}
          />
        </SlideOver>
      )}

      {isMaster && editingEntity && isWorldEntity && (
        <SlideOver
          open
          title={editorTitle}
          description="Lore y vínculos del mundo. Shadow Master recibe estos datos en modo campaña."
          onClose={closeEditor}
        >
          <WorldEntityEditor
            key={`${editingEntity.id}-${editingEntity.updated_at}`}
            campaignId={campaignId}
            entity={editingEntity}
            entities={entities}
            onSaved={handleSaved}
            onCancel={closeEditor}
          />
        </SlideOver>
      )}

      {isMaster && (
        <>
          <CreateEntityForm
            campaignId={campaignId}
            members={members}
            entities={entities}
            gameSystem={gameSystem}
            onNpcCreated={(entity) => openEditor(entity.id, "create")}
          />
          <ImportExportPanel campaignId={campaignId} />
        </>
      )}
    </div>
  );
}
