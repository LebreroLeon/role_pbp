import { useState } from "react";
import { useParams } from "react-router-dom";

import { SECTION_ICONS } from "../components/icons";
import { Panel, PanelHeader, SlideOver, Toast, Button, ErrorBanner } from "../components/ui";
import { EntitySheetEditor } from "../features/character-sheet/EntitySheetEditor";
import { CreateEntityForm, EntityList, ImportExportPanel, WorldEntityEditor, ArcManifestEditor } from "../features/entities";
import { ENTITY_TYPE_LABELS, buildArcManifestDocument, getEntityDisplayName } from "../features/entities/entityDefaults";
import { useCreateEntityMutation, useDeleteEntityMutation } from "../hooks/mutations/useEntityMutations";
import { useCampaignMembersQuery, useCampaignQuery } from "../hooks/queries/useCampaignQueries";
import { useEntitiesQuery } from "../hooks/queries/useEntityQueries";

export function WorldPage() {
  const { campaignId = "" } = useParams();
  const { data: campaign } = useCampaignQuery(campaignId);
  const { data: members = [] } = useCampaignMembersQuery(campaignId);
  const { data: entities = [] } = useEntitiesQuery(campaignId);
  const deleteMutation = useDeleteEntityMutation(campaignId);
  const createArcMutation = useCreateEntityMutation(campaignId);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [editingEntityId, setEditingEntityId] = useState<string | null>(null);
  const [editorMode, setEditorMode] = useState<"create" | "edit">("edit");
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const isMaster = campaign?.role === "MASTER";
  const gameSystem = campaign?.game_system ?? "generic";
  const arcManifest = entities.find((entity) => entity.entity_type === "ARC_MANIFEST") ?? null;
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
    editingEntity?.entity_type === "RELATIONSHIP" ||
    editingEntity?.entity_type === "ARC_MANIFEST";

  async function handleCreateArcManifest() {
    if (arcManifest) return;
    try {
      const created = await createArcMutation.mutateAsync({
        entity_type: "ARC_MANIFEST",
        document: buildArcManifestDocument(),
      });
      openEditor(created.id, "create");
    } catch {
      // ApiError shown via mutation state if needed
    }
  }

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
        {isMaster && (
          <div className="world-arc-panel">
            {arcManifest ? (
              <p className="muted">
                Arco narrativo: <strong>{getEntityDisplayName(arcManifest, entities)}</strong>
                {" · "}
                <button type="button" className="link-button" onClick={() => openEditor(arcManifest.id, "edit")}>
                  Editar macrotrama
                </button>
              </p>
            ) : (
              <div className="world-arc-panel__create">
                <p className="muted">
                  Sin arco narrativo. Shadow Master usa este documento para la macrotrama y misiones activas.
                </p>
                <Button onClick={handleCreateArcManifest} disabled={createArcMutation.isPending}>
                  {createArcMutation.isPending ? "Creando..." : "Crear arco narrativo"}
                </Button>
                {createArcMutation.error && (
                  <ErrorBanner message={createArcMutation.error instanceof Error ? createArcMutation.error.message : "Error al crear arco"} />
                )}
              </div>
            )}
          </div>
        )}
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
            entities={entities}
            mode={editorMode}
            onSaved={handleSaved}
            onCancel={closeEditor}
          />
        </SlideOver>
      )}

      {isMaster && editingEntity && isWorldEntity && editingEntity.entity_type !== "ARC_MANIFEST" && (
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

      {isMaster && editingEntity?.entity_type === "ARC_MANIFEST" && (
        <SlideOver
          open
          title={editorTitle || "Editar arco narrativo"}
          description="Macrotrama, misiones activas y notas secretas para Shadow Master."
          onClose={closeEditor}
        >
          <ArcManifestEditor
            key={`${editingEntity.id}-${editingEntity.updated_at}`}
            campaignId={campaignId}
            entity={editingEntity}
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
