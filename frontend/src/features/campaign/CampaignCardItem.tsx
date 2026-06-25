import { useState } from "react";
import { Link } from "react-router-dom";
import { ChevronRight, Crown, Pencil, Scroll } from "lucide-react";

import type { Campaign } from "../../api/types";
import { useOpenSceneQuery } from "../../hooks/queries/useSceneQueries";
import { CampaignEditModal } from "./CampaignEditModal";
import { CampaignStatusBadges } from "./CampaignStatusBadges";

type CampaignCardItemProps = {
  campaign: Campaign;
};

export function CampaignCardItem({ campaign }: CampaignCardItemProps) {
  const isMaster = campaign.role === "MASTER";
  const [editOpen, setEditOpen] = useState(false);
  const { data: openScene } = useOpenSceneQuery(campaign.id);

  return (
    <li>
      <div className="campaign-card">
        <Link to={`/campaigns/${campaign.id}`} className="campaign-card__nav">
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
              <CampaignStatusBadges
                campaign={campaign}
                openScene={openScene}
                className="campaign-card__badges"
              />
            </div>
          </div>
          <ChevronRight className="campaign-card__chevron" size={18} aria-hidden />
        </Link>
        {isMaster && (
          <button
            type="button"
            className="campaign-card__edit"
            aria-label={`Editar campaña ${campaign.name}`}
            onClick={() => setEditOpen(true)}
          >
            <Pencil size={16} strokeWidth={2} aria-hidden />
          </button>
        )}
      </div>
      {editOpen && <CampaignEditModal campaign={campaign} onClose={() => setEditOpen(false)} />}
    </li>
  );
}
