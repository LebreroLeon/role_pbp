import type { Scene, ScenePickerItem, SceneStatusType } from "../../api/types";
import { StatusBadge } from "../../components/ui";
import { useCampaignScenesQuery } from "../../hooks/queries/useSceneQueries";

const STATUS_LABELS: Record<SceneStatusType, string> = {
  PREPARED: "Preparada",
  ACTIVE: "Activa (abierta)",
  PAUSED: "Pausada (congelada)",
  CLOSED: "Cerrada",
};

export function formatSceneLabel(scene: Pick<Scene, "scene_number" | "display_name">): string {
  if (scene.scene_number == null) {
    return scene.display_name?.trim() || "Escena preparada";
  }
  const prefix = `Escena ${scene.scene_number}`;
  return scene.display_name ? `${prefix}: ${scene.display_name}` : prefix;
}

export function formatPreparedScenePickerLabel(scene: Pick<ScenePickerItem, "scene_number" | "display_name">): string {
  if (scene.scene_number == null) {
    return scene.display_name?.trim() || "Escena preparada";
  }
  const prefix = `Escena ${scene.scene_number}`;
  return scene.display_name ? `${prefix}: ${scene.display_name}` : prefix;
}

type CampaignSceneLogProps = {
  campaignId: string;
  activeSceneId?: string | null;
  isMaster?: boolean;
};

export function CampaignSceneLog({ campaignId, activeSceneId }: CampaignSceneLogProps) {
  const { data: scenes = [], isLoading, isError } = useCampaignScenesQuery(campaignId);

  const closedScenes = scenes.filter((scene) => scene.status === "CLOSED");
  const closedCount = closedScenes.length;
  const orderedScenes = [...scenes].sort(
    (a, b) => (b.scene_number ?? -1) - (a.scene_number ?? -1),
  );
  const latestClosed = closedScenes.reduce<Scene | null>((latest, scene) => {
    if (!latest) return scene;
    return (scene.scene_number ?? -1) > (latest.scene_number ?? -1) ? scene : latest;
  }, null);

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
            </li>
          );
        })}
      </ol>
    </div>
  );
}
