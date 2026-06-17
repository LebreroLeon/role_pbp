import type { Scene, SceneStatusType } from "../../api/types";
import { StatusBadge } from "../../components/ui";
import { useCampaignScenesQuery } from "../../hooks/queries/useSceneQueries";

const STATUS_LABELS: Record<SceneStatusType, string> = {
  ACTIVE: "Activa",
  PAUSED: "Pausada",
  CLOSED: "Cerrada",
};

export function formatSceneLabel(scene: Pick<Scene, "scene_number" | "display_name">): string {
  const prefix = `Escena ${scene.scene_number}`;
  return scene.display_name ? `${prefix}: ${scene.display_name}` : prefix;
}

type CampaignSceneLogProps = {
  campaignId: string;
  activeSceneId?: string | null;
};

export function CampaignSceneLog({ campaignId, activeSceneId }: CampaignSceneLogProps) {
  const { data: scenes = [], isLoading, isError } = useCampaignScenesQuery(campaignId);

  const closedCount = scenes.filter((scene) => scene.status === "CLOSED").length;
  const orderedScenes = [...scenes].sort((a, b) => b.scene_number - a.scene_number);

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
      <div className="status-row scene-log__summary">
        <StatusBadge label="Escenas cerradas" value={String(closedCount)} ok={closedCount > 0} />
        <StatusBadge label="Total" value={String(scenes.length)} ok />
      </div>

      <ol className="scene-log__list">
        {orderedScenes.map((scene) => {
          const isCurrent = scene.id === activeSceneId;
          return (
            <li
              key={scene.id}
              className={`scene-log__item scene-log__item--${scene.status.toLowerCase()}${isCurrent ? " is-current" : ""}`}
            >
              <div className="scene-log__header">
                <strong>{formatSceneLabel(scene)}</strong>
                <span className={`scene-log__status scene-log__status--${scene.status.toLowerCase()}`}>
                  {STATUS_LABELS[scene.status as SceneStatusType] ?? scene.status}
                  {isCurrent ? " · actual" : ""}
                </span>
              </div>
              {scene.status === "CLOSED" && scene.summary && (
                <p className="scene-log__summary-text muted">{scene.summary}</p>
              )}
            </li>
          );
        })}
      </ol>
    </div>
  );
}
