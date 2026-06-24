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
  Toast,
} from "../../components/ui";
import { formatSceneLabel } from "../campaign";
import { useCampaignScenesQuery, useOpenSceneQuery } from "../../hooks/queries/useSceneQueries";
import { useEntitiesQuery } from "../../hooks/queries/useEntityQueries";
import { getChatBuffer } from "./sceneState";
import { ScenePrepEditor } from "./ScenePrepEditor";
import { MasterBriefingModal } from "./MasterBriefingModal";
import { NextSceneModal } from "./NextSceneModal";

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

function compareScenes(a: Scene, b: Scene): number {
  const orderDiff = (STATUS_SORT_ORDER[a.status] ?? 99) - (STATUS_SORT_ORDER[b.status] ?? 99);
  if (orderDiff !== 0) return orderDiff;
  const aNumber = a.scene_number ?? -1;
  const bNumber = b.scene_number ?? -1;
  if (aNumber !== bNumber) return bNumber - aNumber;
  return a.display_name?.localeCompare(b.display_name ?? "", "es") ?? 0;
}

export function PreparedScenesPanel({ campaignId, onSceneClosed }: PreparedScenesPanelProps) {
  const queryClient = useQueryClient();
  const { data: scenes = [], refetch } = useCampaignScenesQuery(campaignId);
  const { data: openScene } = useOpenSceneQuery(campaignId);
  const { data: entities = [] } = useEntitiesQuery(campaignId);

  const [error, setError] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [editingScene, setEditingScene] = useState<Scene | null>(null);
  const [saving, setSaving] = useState(false);
  const [loadingBriefingId, setLoadingBriefingId] = useState<string | null>(null);
  const [activatingId, setActivatingId] = useState<string | null>(null);
  const [briefing, setBriefing] = useState<MasterBriefingResponse | null>(null);
  const [sendOpening, setSendOpening] = useState(true);
  const [freezing, setFreezing] = useState(false);
  const [closing, setClosing] = useState(false);
  const [closeDialogOpen, setCloseDialogOpen] = useState(false);
  const [nextSceneOpen, setNextSceneOpen] = useState(false);
  const [preparedScenes, setPreparedScenes] = useState<ScenePickerItem[]>([]);
  const [closedSceneSummary, setClosedSceneSummary] = useState<string | null>(null);
  const [nextSceneLoading, setNextSceneLoading] = useState(false);

  const sortedScenes = useMemo(() => [...scenes].sort(compareScenes), [scenes]);
  const preparedCount = useMemo(() => scenes.filter((scene) => scene.status === "PREPARED").length, [scenes]);

  async function invalidate() {
    await queryClient.invalidateQueries({ queryKey: queryKeys.campaigns.scenes(campaignId) });
    await queryClient.invalidateQueries({ queryKey: queryKeys.campaigns.activeScene(campaignId) });
  }

  async function handleCreatePrepared() {
    setCreating(true);
    setError(null);
    try {
      const created = await api.createScene(campaignId, {
        displayName: `Preparada ${preparedCount + 1}`,
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
    setLoadingBriefingId(scene.id);
    setError(null);
    try {
      const data = await api.getMasterBriefing(campaignId, scene.id);
      setBriefing(data);
      setSendOpening(Boolean(data.opening_narration?.trim()));
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo cargar el briefing");
    } finally {
      setLoadingBriefingId(null);
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
      setEditingScene(null);
      await invalidate();
      setToastMessage(`Escena ${activated.scene_number} activada.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo activar la escena");
    } finally {
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
      setPreparedScenes(result.prepared_scenes);
      setClosedSceneSummary(result.closed_scene.summary ?? null);
      setNextSceneOpen(true);
      onSceneClosed?.(result.prepared_scenes);
      setToastMessage("Escena cerrada y resumen generado.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo cerrar la escena");
    } finally {
      setClosing(false);
    }
  }

  async function handlePickPreparedScene(sceneId: string) {
    setNextSceneLoading(true);
    setError(null);
    try {
      const data = await api.getMasterBriefing(campaignId, sceneId);
      setNextSceneOpen(false);
      setBriefing(data);
      setSendOpening(Boolean(data.opening_narration?.trim()));
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo cargar el briefing");
    } finally {
      setNextSceneLoading(false);
    }
  }

  async function handleCreateNextScene(displayName: string, objective: string) {
    setNextSceneLoading(true);
    setError(null);
    try {
      const created = await api.createScene(campaignId, {
        displayName: displayName || undefined,
        sceneObjective: objective,
      });
      queryClient.setQueryData(queryKeys.campaigns.activeScene(campaignId), created);
      await invalidate();
      setNextSceneOpen(false);
      setPreparedScenes([]);
      setToastMessage(`Escena ${created.scene_number} creada y activada.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo crear la escena");
    } finally {
      setNextSceneLoading(false);
    }
  }

  function renderSceneRow(scene: Scene) {
    const current = isCurrentScene(scene, openScene);
    const showMessages = current && (scene.status === "ACTIVE" || scene.status === "PAUSED");
    const messageCount = getChatBuffer(scene.scene_state).length;
    const loadingBriefing = loadingBriefingId === scene.id;

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
            {scene.status === "PREPARED" && scene.scene_number == null && (
              <StatusBadge label="Número" value="—" ok={false} />
            )}
            {showMessages && <StatusBadge label="Mensajes" value={String(messageCount)} ok />}
          </div>
          {quickActions}
        </div>
        <div className="prepared-scenes__row-actions">
          <Button variant="secondary" onClick={() => setEditingScene(scene)}>
            Editar
          </Button>
          {!current && scene.status === "PREPARED" && (
            <Button onClick={() => handleRequestActivate(scene)} disabled={loadingBriefing || activatingId === scene.id}>
              {loadingBriefing ? "Cargando…" : "Activar"}
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
              {openScene && (
                <p>
                  Se cerrará <strong>{formatSceneLabel(openScene)}</strong> de forma permanente.
                </p>
              )}
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

      {nextSceneOpen && (
        <NextSceneModal
          preparedScenes={preparedScenes}
          loading={nextSceneLoading}
          closedSceneSummary={closedSceneSummary}
          onPickPrepared={handlePickPreparedScene}
          onCreateNew={handleCreateNextScene}
          onCancel={() => {
            setNextSceneOpen(false);
            setPreparedScenes([]);
            setClosedSceneSummary(null);
          }}
          onCloseOnly={() => {
            setNextSceneOpen(false);
            setPreparedScenes([]);
            setClosedSceneSummary(null);
          }}
        />
      )}

      <Toast message={toastMessage} onDismiss={() => setToastMessage(null)} />
    </section>
  );
}
