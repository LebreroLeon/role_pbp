import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { api } from "../../api/client";
import { queryKeys } from "../../api/queryKeys";
import type { Scene, SceneStatusType } from "../../api/types";
import { Button, StatusBadge } from "../../components/ui";
import { useCampaignScenesQuery } from "../../hooks/queries/useSceneQueries";

const STATUS_LABELS: Record<SceneStatusType, string> = {
  PREPARED: "Preparada",
  ACTIVE: "Activa (abierta)",
  PAUSED: "Pausada (congelada)",
  CLOSED: "Cerrada",
};

export function formatSceneLabel(scene: Pick<Scene, "scene_number" | "display_name">): string {
  const prefix = `Escena ${scene.scene_number}`;
  return scene.display_name ? `${prefix}: ${scene.display_name}` : prefix;
}

type CampaignSceneLogProps = {
  campaignId: string;
  activeSceneId?: string | null;
  isMaster?: boolean;
};

export function CampaignSceneLog({ campaignId, activeSceneId, isMaster = false }: CampaignSceneLogProps) {
  const queryClient = useQueryClient();
  const { data: scenes = [], isLoading, isError } = useCampaignScenesQuery(campaignId);
  const [resumingId, setResumingId] = useState<string | null>(null);
  const [resumeError, setResumeError] = useState<string | null>(null);

  const closedScenes = scenes.filter((scene) => scene.status === "CLOSED");
  const closedCount = closedScenes.length;
  const orderedScenes = [...scenes].sort((a, b) => b.scene_number - a.scene_number);
  const latestClosed = closedScenes.reduce<Scene | null>(
    (latest, scene) => (!latest || scene.scene_number > latest.scene_number ? scene : latest),
    null,
  );

  async function handleResume(sceneId: string) {
    setResumingId(sceneId);
    setResumeError(null);
    try {
      const updated = await api.activateScene(campaignId, sceneId);
      queryClient.setQueryData(queryKeys.campaigns.activeScene(campaignId), updated);
      await queryClient.invalidateQueries({ queryKey: queryKeys.campaigns.scenes(campaignId) });
    } catch (err) {
      setResumeError(err instanceof Error ? err.message : "No se pudo reanudar la escena");
    } finally {
      setResumingId(null);
    }
  }

  if (isLoading) {
    return <p className="muted">Cargando historial de escenas...</p>;
  }

  if (isError) {
    return <p className="muted">No se pudo cargar el historial de escenas.</p>;
  }

  if (orderedScenes.length === 0) {
    return <p className="muted hub-hint">Aún no hay escenas registradas en esta campaña.</p>;
  }

  return (
    <div className="scene-log">
      {latestClosed && (
        <div className="scene-log__latest-closed">
          <p className="scene-log__latest-label">Última escena cerrada</p>
          <strong>{formatSceneLabel(latestClosed)}</strong>
          {latestClosed.summary ? (
            <p className="scene-log__summary-text">{latestClosed.summary}</p>
          ) : (
            <p className="scene-log__summary-missing muted">Sin resumen registrado.</p>
          )}
        </div>
      )}

      <div className="status-row scene-log__summary">
        <StatusBadge label="Escenas cerradas" value={String(closedCount)} ok={closedCount > 0} />
        <StatusBadge label="Total" value={String(scenes.length)} ok />
      </div>

      {resumeError && <p className="muted scene-log__error">{resumeError}</p>}

      <ol className="scene-log__list">
        {orderedScenes.map((scene) => {
          const isCurrent = scene.status === "ACTIVE" && scene.id === activeSceneId;
          const status = scene.status as SceneStatusType;
          return (
            <li
              key={scene.id}
              className={`scene-log__item scene-log__item--${scene.status.toLowerCase()}${isCurrent ? " is-current" : ""}`}
            >
              <div className="scene-log__header">
                <div className="scene-log__title-row">
                  <strong>{formatSceneLabel(scene)}</strong>
                  {isCurrent && <span className="scene-log__current-badge">Escena actual</span>}
                </div>
                <span className={`scene-log__status scene-log__status--${scene.status.toLowerCase()}`}>
                  {STATUS_LABELS[status] ?? scene.status}
                </span>
              </div>
              {scene.status === "CLOSED" && (
                scene.summary ? (
                  <p className="scene-log__summary-text">{scene.summary}</p>
                ) : (
                  <p className="scene-log__summary-missing muted">Sin resumen registrado.</p>
                )
              )}
              {isMaster && scene.status === "PAUSED" && (
                <div className="scene-log__actions">
                  <Button
                    variant="secondary"
                    onClick={() => handleResume(scene.id)}
                    disabled={resumingId === scene.id}
                  >
                    {resumingId === scene.id ? "Reanudando…" : "Reanudar"}
                  </Button>
                </div>
              )}
            </li>
          );
        })}
      </ol>
    </div>
  );
}
