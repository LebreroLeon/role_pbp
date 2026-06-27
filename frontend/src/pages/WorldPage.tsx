import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { Activity, Plus, SECTION_ICONS, Swords } from "../components/icons";
import { SlideOver, Toast, Button, ErrorBanner, CollapsibleSection } from "../components/ui";
import { EntitySheetEditor } from "../features/character-sheet/EntitySheetEditor";
import { CampaignSceneLog, formatSceneLabel } from "../features/campaign";
import { CreateEntityForm, EntityList, ImportExportPanel, MonsterSpawnPanel, WorldEntityEditor, ArcManifestEditor } from "../features/entities";
import { ENTITY_TYPE_LABELS, buildArcManifestDocument, getEntityDisplayName } from "../features/entities/entityDefaults";
import { WORLD_VIEW_TAB_LABELS, type WorldViewFilter } from "../features/entities/compendiumTier";
import { useCreateEntityMutation, useDeleteEntityMutation } from "../hooks/mutations/useEntityMutations";
import { useCampaignMembersQuery, useCampaignQuery } from "../hooks/queries/useCampaignQueries";
import { useEntitiesQuery } from "../hooks/queries/useEntityQueries";
import { useOpenSceneQuery } from "../hooks/queries/useSceneQueries";

const WORLD_VIEW_TABS: { id: WorldViewFilter; label: string }[] = (
  Object.entries(WORLD_VIEW_TAB_LABELS) as [WorldViewFilter, string][]
).map(([id, label]) => ({ id, label }));

export function WorldPage() {
  const { campaignId = "" } = useParams();
  const base = `/campaigns/${campaignId}`;
  const { data: campaign } = useCampaignQuery(campaignId);
  const { data: members = [] } = useCampaignMembersQuery(campaignId);
  const { data: entities = [] } = useEntitiesQuery(campaignId);
  const { data: openScene } = useOpenSceneQuery(campaignId);
  const deleteMutation = useDeleteEntityMutation(campaignId);
  const createArcMutation = useCreateEntityMutation(campaignId);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [editingEntityId, setEditingEntityId] = useState<string | null>(null);
  const [editorMode, setEditorMode] = useState<"create" | "edit">("edit");
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [worldView, setWorldView] = useState<WorldViewFilter>("story");
  const [createEntityOpen, setCreateEntityOpen] = useState(false);

  const isMaster = campaign?.role === "MASTER";
  const gameSystem = campaign?.game_system ?? "generic";
  const arcManifest = entities.find((entity) => entity.entity_type === "ARC_MANIFEST") ?? null;
  const editingEntity = editingEntityId ? entities.find((entity) => entity.id === editingEntityId) ?? null : null;
  const closedScenesHint = openScene ? formatSceneLabel(openScene) : null;

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

      <CollapsibleSection
        icon={Activity}
        iconTone="teal"
        title="Historial de escenas"
        description={
          isMaster
            ? "Compendio de resúmenes y escena en curso. Reanuda escenas pausadas desde aquí."
            : "Resúmenes de escenas que ya vivió la mesa y la escena actual."
        }
      >
        {!openScene && (
          <p className="muted hub-hint">
            {isMaster ? (
              <>
                Aún no hay escena activa. Ve a <Link to={`${base}/chat`}>Jugar</Link> para iniciarla.
              </>
            ) : (
              "Esperando al Máster. El Máster debe iniciar la siguiente escena antes de que puedas entrar al chat."
            )}
          </p>
        )}
        {openScene && closedScenesHint && (
          <p className="muted hub-hint">
            Escena en curso: <strong>{closedScenesHint}</strong>
            {" · "}
            <Link to={`${base}/chat`}>Ir a Jugar</Link>
          </p>
        )}
        <CampaignSceneLog campaignId={campaignId} activeSceneId={openScene?.id} isMaster={isMaster} />
      </CollapsibleSection>

      <CollapsibleSection
        icon={SECTION_ICONS.mundo}
        iconTone="violet"
        title="Mundo"
        description={
          isMaster
            ? "Compendio narrativo: NPCs relevantes, localizaciones, facciones y relaciones. El bestiario de combate vive en su propia pestaña."
            : "Personajes y lugares que tu PJ conoce. Los secretos del Máster no se muestran aquí."
        }
        defaultOpen={isMaster}
      >
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

        {isMaster && (
          <div className="world-toolbar">
            <div className="world-view-tabs" role="tablist" aria-label="Vista del compendio">
              {WORLD_VIEW_TABS.map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  role="tab"
                  aria-selected={worldView === tab.id}
                  className={`world-view-tabs__tab${worldView === tab.id ? " is-active" : ""}`}
                  onClick={() => setWorldView(tab.id)}
                >
                  {tab.label}
                </button>
              ))}
            </div>
            <Button className="world-toolbar__add" onClick={() => setCreateEntityOpen(true)}>
              <Plus size={16} aria-hidden />
              Añadir entidad
            </Button>
          </div>
        )}

        {isMaster && worldView === "combat" && (
          <CollapsibleSection
            icon={Swords}
            iconTone="rose"
            title="Invocar del catálogo SRD"
            description="Busca en el bestiario y añade monstruos con ficha D&D 5e."
            defaultOpen={false}
            className="world-bestiario-spawn"
          >
            <MonsterSpawnPanel
              campaignId={campaignId}
              gameSystem={gameSystem}
              onSpawned={setToastMessage}
              embedded
            />
          </CollapsibleSection>
        )}

        <EntityList
          campaignId={campaignId}
          entities={entities}
          isMaster={Boolean(isMaster)}
          viewFilter={isMaster ? worldView : "story"}
          onEdit={isMaster ? (entity) => openEditor(entity.id, "edit") : undefined}
          editingId={editingEntityId}
          onDelete={isMaster ? handleDelete : undefined}
          deletingId={deletingId}
        />

        {isMaster && (
          <CollapsibleSection
            title="Importar / exportar"
            description="Copia de seguridad del compendio en JSON."
            defaultOpen={false}
            className="world-import-export"
          >
            <ImportExportPanel campaignId={campaignId} embedded />
          </CollapsibleSection>
        )}
      </CollapsibleSection>

      {isMaster && createEntityOpen && (
        <SlideOver
          open
          title="Nueva entidad del mundo"
          description="Añade NPCs, localizaciones, facciones, relaciones o el PJ de un jugador."
          onClose={() => setCreateEntityOpen(false)}
        >
          <CreateEntityForm
            campaignId={campaignId}
            members={members}
            entities={entities}
            gameSystem={gameSystem}
            embedded
            onCancel={() => setCreateEntityOpen(false)}
            onNpcCreated={(entity) => {
              setCreateEntityOpen(false);
              openEditor(entity.id, "create");
            }}
            onCreated={() => {
              setCreateEntityOpen(false);
              setToastMessage("Entidad creada correctamente.");
            }}
          />
        </SlideOver>
      )}

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
    </div>
  );
}
