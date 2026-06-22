import { useMemo, useState, type ReactNode } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { api } from "../../api/client";
import { queryKeys } from "../../api/queryKeys";
import type { MasterBriefingResponse, Scene } from "../../api/types";
import { Button, ErrorBanner, SlideOver, StatusBadge } from "../../components/ui";
import { formatSceneLabel } from "../campaign";
import { useCampaignScenesQuery } from "../../hooks/queries/useSceneQueries";
import { useEntitiesQuery } from "../../hooks/queries/useEntityQueries";
import { getSceneObjective } from "./sceneState";
import { ScenePrepEditor } from "./ScenePrepEditor";
import { MasterBriefingModal } from "./MasterBriefingModal";

type PreparedScenesPanelProps = {
  campaignId: string;
};

const STATUS_LABELS: Record<string, string> = {
  PREPARED: "Preparada",
  ACTIVE: "Activa",
  PAUSED: "Pausada",
  CLOSED: "Cerrada",
};

export function PreparedScenesPanel({ campaignId }: PreparedScenesPanelProps) {
  const queryClient = useQueryClient();
  const { data: scenes = [], refetch } = useCampaignScenesQuery(campaignId);
  const { data: entities = [] } = useEntitiesQuery(campaignId);

  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [editingScene, setEditingScene] = useState<Scene | null>(null);
  const [saving, setSaving] = useState(false);
  const [activatingId, setActivatingId] = useState<string | null>(null);
  const [briefing, setBriefing] = useState<MasterBriefingResponse | null>(null);
  const [sendOpening, setSendOpening] = useState(true);

  const grouped = useMemo(() => {
    const prepared = scenes.filter((scene) => scene.status === "PREPARED");
    const active = scenes.filter((scene) => scene.status === "ACTIVE" || scene.status === "PAUSED");
    const closed = scenes.filter((scene) => scene.status === "CLOSED");
    return { prepared, active, closed };
  }, [scenes]);

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
      const updated = await api.updateScenePrep(editingScene.id, payload);
      setEditingScene(updated);
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

  function renderSceneRow(scene: Scene, actions?: ReactNode) {
    return (
      <li key={scene.id} className="prepared-scenes__row">
        <div>
          <strong>{formatSceneLabel(scene)}</strong>
          <p className="muted">{getSceneObjective(scene.scene_state) ?? "Sin objetivo"}</p>
        </div>
        <div className="prepared-scenes__row-meta">
          <StatusBadge label="Estado" value={STATUS_LABELS[scene.status] ?? scene.status} ok={scene.status === "ACTIVE"} />
          {actions}
        </div>
      </li>
    );
  }

  return (
    <section className="prepared-scenes">
      {error && <ErrorBanner message={error} />}

      <div className="actions">
        <Button onClick={handleCreatePrepared} disabled={creating}>
          {creating ? "Creando…" : "Nueva escena preparada"}
        </Button>
        <Button variant="secondary" onClick={() => refetch()}>
          Actualizar
        </Button>
      </div>

      <h3>Preparadas</h3>
      {grouped.prepared.length === 0 ? (
        <p className="muted">Sin escenas preparadas. Crea ramas (Puerta A / Puerta B) antes de jugar.</p>
      ) : (
        <ul className="prepared-scenes__list">
          {grouped.prepared.map((scene) =>
            renderSceneRow(
              scene,
              <>
                <Button variant="secondary" onClick={() => setEditingScene(scene)}>
                  Editar
                </Button>
                <Button onClick={() => handleRequestActivate(scene)} disabled={activatingId === scene.id}>
                  Activar
                </Button>
              </>,
            ),
          )}
        </ul>
      )}

      <h3>Activas / pausadas</h3>
      {grouped.active.length === 0 ? (
        <p className="muted">Ninguna escena en juego.</p>
      ) : (
        <ul className="prepared-scenes__list">
          {grouped.active.map((scene) => renderSceneRow(scene))}
        </ul>
      )}

      <h3>Cerradas</h3>
      {grouped.closed.length === 0 ? (
        <p className="muted">Sin historial aún.</p>
      ) : (
        <ul className="prepared-scenes__list prepared-scenes__list--closed">
          {grouped.closed.slice(-5).reverse().map((scene) => renderSceneRow(scene))}
        </ul>
      )}

      {editingScene && (
        <SlideOver
          open
          title={`Preparar — ${formatSceneLabel(editingScene)}`}
          description="Objetivo, ubicación, apertura y entidades planificadas"
          onClose={() => setEditingScene(null)}
        >
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
    </section>
  );
}
