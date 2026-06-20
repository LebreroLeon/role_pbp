import type { Campaign, Scene } from "../../api/types";
import { StatusBadge } from "../../components/ui";
import { useCampaignMembersQuery } from "../../hooks/queries/useCampaignQueries";
import { useCampaignScenesQuery } from "../../hooks/queries/useSceneQueries";
import { gameSystemLabel } from "./gameSystems";

type CampaignStatusBadgesProps = {
  campaign: Campaign;
  openScene?: Scene | null;
  showSceneCounts?: boolean;
  className?: string;
};

function partidaStatus(openScene?: Scene | null): { value: string; ok: boolean } {
  if (!openScene) return { value: "Sin escena", ok: false };
  if (openScene.status === "ACTIVE") return { value: "En curso", ok: true };
  if (openScene.status === "PAUSED") return { value: "Pausada", ok: false };
  return { value: "Cerrada", ok: false };
}

export function CampaignStatusBadges({
  campaign,
  openScene,
  showSceneCounts = false,
  className = "",
}: CampaignStatusBadgesProps) {
  const { data: members = [] } = useCampaignMembersQuery(campaign.id);
  const { data: scenes = [] } = useCampaignScenesQuery(campaign.id);
  const players = members.filter((member) => member.role === "PLAYER");
  const partida = partidaStatus(openScene);
  const closedCount = scenes.filter((scene) => scene.status === "CLOSED").length;
  const rowClass = ["status-row", "campaign-status-badges", className].filter(Boolean).join(" ");

  return (
    <div className={rowClass}>
      <StatusBadge label="Partida" value={partida.value} ok={partida.ok} />
      <StatusBadge label="Sistema" value={gameSystemLabel(campaign.game_system)} ok />
      <StatusBadge
        label="Escena"
        value={
          openScene
            ? openScene.display_name
              ? `#${openScene.scene_number} · ${openScene.display_name}`
              : `#${openScene.scene_number}`
            : "sin iniciar"
        }
        ok={openScene?.status === "ACTIVE"}
      />
      {openScene && (
        <StatusBadge
          label="Estado"
          value={
            openScene.status === "ACTIVE"
              ? "Activa (abierta)"
              : openScene.status === "PAUSED"
                ? "Pausada (congelada)"
                : "Cerrada"
          }
          ok={openScene.status === "ACTIVE"}
        />
      )}
      <StatusBadge label="Jugadores" value={String(players.length)} ok={players.length > 0} />
      {showSceneCounts && (
        <>
          <StatusBadge label="Escenas cerradas" value={String(closedCount)} ok={closedCount > 0} />
          <StatusBadge label="Total escenas" value={String(scenes.length)} ok={scenes.length > 0} />
        </>
      )}
    </div>
  );
}
