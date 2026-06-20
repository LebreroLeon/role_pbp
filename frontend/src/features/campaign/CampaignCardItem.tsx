import { Link } from "react-router-dom";
import { ChevronRight, Crown, Scroll } from "lucide-react";

import type { Campaign } from "../../api/types";
import { StatusBadge } from "../../components/ui";
import { useCampaignMembersQuery } from "../../hooks/queries/useCampaignQueries";
import { useOpenSceneQuery } from "../../hooks/queries/useSceneQueries";
import { gameSystemLabel } from "./gameSystems";

type CampaignCardItemProps = {
  campaign: Campaign;
};

export function CampaignCardItem({ campaign }: CampaignCardItemProps) {
  const isMaster = campaign.role === "MASTER";
  const { data: members = [] } = useCampaignMembersQuery(campaign.id);
  const { data: openScene } = useOpenSceneQuery(campaign.id);
  const players = members.filter((member) => member.role === "PLAYER");

  return (
    <li>
      <Link to={`/campaigns/${campaign.id}`} className="campaign-card">
        <div className="campaign-card__main">
          <span
            className={`campaign-card__icon ${isMaster ? "campaign-card__icon--master" : ""}`}
            aria-hidden
          >
            {isMaster ? <Crown size={18} strokeWidth={2} /> : <Scroll size={18} strokeWidth={2} />}
          </span>
          <div className="campaign-card__body">
            <strong>{campaign.name}</strong>
            {campaign.tone && <p className="muted">{campaign.tone}</p>}
            <div className="status-row campaign-card__badges">
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
            </div>
          </div>
        </div>
        <ChevronRight className="campaign-card__chevron" size={18} aria-hidden />
      </Link>
    </li>
  );
}
