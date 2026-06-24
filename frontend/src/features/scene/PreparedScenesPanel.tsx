import { useMemo, useState, type ReactNode } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { GitBranch } from "lucide-react";

import { api } from "../../api/client";
import { queryKeys } from "../../api/queryKeys";
import type { MasterBriefingResponse, Scene, ScenePickerItem } from "../../api/types";
import {
  Button,
  ButtonLink,
  ConfirmDialog,
  ErrorBanner,
  PanelHeader,
  SlideOver,
  StatusBadge,
} from "../../components/ui";
import { formatSceneLabel } from "../campaign";
import { useCampaignScenesQuery, useOpenSceneQuery } from "../../hooks/queries/useSceneQueries";
import { useEntitiesQuery } from "../../hooks/queries/useEntityQueries";
import { getChatBuffer } from "./sceneState";
import { ScenePrepEditor } from "./ScenePrepEditor";
import { MasterBriefingModal } from "./MasterBriefingModal";

type PreparedScenesPanelProps = {
  campaignId: string;
  onSceneClosed?: (preparedScenes: ScenePickerItem[]) => void;
};

const STATUS_LABELS: Record<string, string> = {
  PREPARED: "Preparada",
  ACTIVE: "Activa",
  PAUSED: "Pausada",
  CLOSED: "Cerrada",
};

const STATUS_SORT_ORDER: Record<string, number> = {
  ACTIVE: 0,
  PAUSED: 1,
  PREPARED: 2,
  CLOSED: 3,
};

function isCurrentScene(scene: Scene, openScene: Scene | null | undefined): boolean {
  return Boolean(openScene && openScene.id === scene.id);
}

export function PreparedScenesPanel({ campaignId, onSceneClosed }: PreparedScenesPanelProps) {
  const queryClient = useQueryClient();
  const { data: scenes = [], refetch } = useCampaignScenesQuery(campaignId);
  const { data: openScene } = useOpenSceneQuery(campaignId);
  const { data: entities = [] } = useEntitiesQuery(campaignId);

  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [editingScene, setEditingScene] = useState<Scene | null>(null);
  const [saving, setSaving] = useState(false);
  const [activatingId, setActivatingId] = useState<string | null>(null);
  const [briefing, setBriefing] = useState<MasterBriefingResponse | null>(null);
  const [sendOpening, setSendOpening] = useState(true);
  const [freezing, setFreezing] = useState(false);
  const [closing, setClosing] = useState(false);
  const [closeDialogOpen, setCloseDialogOpen] = useState(false);

  const sortedScenes = useMemo(
    () =>
      [...scenes].sort((a, b) => {
        const orderDiff = (STATUS_SORT_ORDER[a.status] ?? 99) - (STATUS_SORT_ORDER[b.status] ?? 99);
        if (orderDiff !== 0) return orderDiff;
        return b.scene_number - a.scene_number;
      }),
    [scenes],
  );

  async function invalidate() {
    await queryClient.invalidateQueries({ queryKey: queryKeys.campaigns.scenes(campaignId) });
    await queryClient.invalidateQueries({ queryKey: queryKeys.campaigns.activeScene(campaignId) });
  }

  async function handleCreatePrepared() {
    setCreating(true);
    setError(null);
    try {
      const created = await api.createScene(campaignId, {
        displayName: `Escena ${scenes.length + 1}`,
        status: "PREPARED",
      });
      await invalidate();
      setEditingScene(created);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo crear la escena");
    } finally {
      setCreating(false);
    }
  }

  async function handleSavePrep(payload: Parameters<typeof api.updateScenePrep>[1]) {
    if (!editingScene) return;
    setSaving(true);
    setError(null);
    try {
      await api.updateScenePrep(editingScene.id, payload);
      setEditingScene(null);
      await invalidate();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo guardar");
    } finally {
      setSaving(false);
    }
  }

  async function handleRequestActivate(scene: Scene) {
    setActivatingId(scene.id);
    setError(null);
    try {
      const data = await api.getMasterBriefing(campaignId, scene.id);
      setBriefing(data);
      setSendOpening(Boolean(data.opening_narration?.trim()));
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo cargar el briefing");
      setActivatingId(null);
    }
  }

  async function handleConfirmActivate() {
    if (!briefing) return;
    setActivatingId(briefing.scene_id);
    setError(null);
    try {
      const activated = await api.activateScene(campaignId, briefing.scene_id, {
        sendOpeningToChat: sendOpening,
      });
      queryClient.setQueryData(queryKeys.campaigns.activeScene(campaignId), activated);
      setBriefing(null);
      setActivatingId(null);
      setEditingScene(null);
      await invalidate();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo activar la escena");
      setActivatingId(null);
    }
  }

  async function handleFreeze() {
    if (!openScene) return;
    setFreezing(true);
    setError(null);
    try {
      const next = openScene.status === "PAUSED" ? "ACTIVE" : "PAUSED";
      const updated = await api.updateSceneStatus(openScene.id, next);
      queryClient.setQueryData(queryKeys.campaigns.activeScene(campaignId), updated);
      await invalidate();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo cambiar el estado");
    } finally {
      setFreezing(false);
    }
  }

  async function handleCloseScene() {
    if (!openScene) return;
    setClosing(true);
    setError(null);
    try {
      const result = await api.closeScene(openScene.id);
      queryClient.removeQueries({ queryKey: queryKeys.campaigns.activeScene(campaignId) });
      await invalidate();
      setCloseDialogOpen(false);
      onSceneClosed?.(result.prepared_scenes);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo cerrar la escena");
    } finally {
      setClosing(false);
    }
  }

  function renderSceneRow(scene: Scene) {
    const current = isCurrentScene(scene, openScene);
    const showMessages = current && (scene.status === "ACTIVE" || scene.status === "PAUSED");
    const messageCount = getChatBuffer(scene.scene_state).length;

    let quickActions: ReactNode = null;
    if (current && (scene.status === "ACTIVE" || scene.status === "PAUSED")) {
      quickActions = (
        <div className="prepared-scenes__quick-actions">
          <ButtonLink to={`/campaigns/${campaignId}/chat`} variant="secondary">
            Ir a Jugar
          </ButtonLink>
          <Button variant="secondary" onClick={handleFreeze} disabled={freezing}>
            {scene.status === "PAUSED" ? "Reanudar" : "Congelar"}
          </Button>
          <Button variant="secondary" onClick={() => setCloseDialogOpen(true)} disabled={closing}>
            Cerrar
          </Button>
        </div>
      );
    }

    return (
      <li key={scene.id} className={`prepared-scenes__row${current ? " prepared-scenes__row--current" : ""}`}>
        <div className="prepared-scenes__row-main">
          <strong className="prepared-scenes__row-title">{formatSceneLabel(scene)}</strong>
          <div className="prepared-scenes__row-meta">
            <StatusBadge
              label="Estado"
              value={STATUS_LABELS[scene.status] ?? scene.status}
              ok={scene.status === "ACTIVE"}
            />
            {showMessages && <StatusBadge label="Mensajes" value={String(messageCount)} ok />}
          </div>
          {quickActions}
        </div>
        <div className="prepared-scenes__row-actions">
          <Button variant="secondary" onClick={() => setEditingScene(scene)}>
            Editar
          </Button>
          {!current && (
            <Button onClick={() => handleRequestActivate(scene)} disabled={activatingId === scene.id}>
              Activar
            </Button>
          )}
        </div>
      </li>
    );
  }

  return (
    <section className="prepared-scenes">
      {error && <ErrorBanner message={error} />}

      <PanelHeader
        icon={GitBranch}
        iconTone="teal"
        title="Escenas"
        description="Todas las escenas de la campaña: preparadas, en curso y cerradas."
        actions={
          <div className="prepared-scenes__header-actions">
            <Button onClick={handleCreatePrepared} disabled={creating}>
              {creating ? "Creando…" : "+ Añadir Escena"}
            </Button>
            <Button variant="secondary" onClick={() => refetch()}>
              Actualizar
            </Button>
          </div>
        }
      />

      {sortedScenes.length === 0 ? (
        <p className="muted">Sin escenas. Usa «+ Añadir Escena» para preparar la primera.</p>
      ) : (
        <ul className="prepared-scenes__list">{sortedScenes.map((scene) => renderSceneRow(scene))}</ul>
      )}

      {editingScene && (
        <SlideOver open title="Editar escena" onClose={() => setEditingScene(null)}>
          <ScenePrepEditor
            scene={editingScene}
            entities={entities}
            saving={saving}
            error={error}
            onSave={handleSavePrep}
          />
        </SlideOver>
      )}

      {briefing && (
        <MasterBriefingModal
          briefing={briefing}
          activating={activatingId === briefing.scene_id}
          sendOpening={sendOpening}
          onSendOpeningChange={setSendOpening}
          onActivate={handleConfirmActivate}
          onCancel={() => {
            setBriefing(null);
            setActivatingId(null);
          }}
        />
      )}

      {closeDialogOpen && (
        <ConfirmDialog
          title="Cerrar escena"
          description={
            <>
              <p>
                Se enviará todo el chat de la escena a la IA para generar un resumen narrativo en español (WorldLog).
              </p>
              <p className="muted">
                El resumen quedará en el historial de escenas y en la memoria de campaña. Esta acción no se puede
                deshacer.
              </p>
            </>
          }
          confirmLabel="Cerrar y generar resumen"
          onConfirm={handleCloseScene}
          onCancel={() => setCloseDialogOpen(false)}
          confirming={closing}
        />
      )}
    </section>
  );
}
