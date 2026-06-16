import { Link } from "react-router-dom";
import { ChevronRight, Crown, Scroll } from "lucide-react";

import type { Campaign } from "../../api/types";
import { StatusBadge } from "../../components/ui";

type CampaignListProps = {
  campaigns: Campaign[];
};

export function CampaignList({ campaigns }: CampaignListProps) {
  if (campaigns.length === 0) {
    return <p className="muted">Aún no perteneces a ninguna campaña. Crea una nueva abajo.</p>;
  }

  return (
    <ul className="campaign-list">
      {campaigns.map((campaign) => {
        const isMaster = campaign.role === "MASTER";
        return (
          <li key={campaign.id}>
            <Link to={`/campaigns/${campaign.id}`} className="campaign-card">
              <div className="campaign-card__main">
                <span
                  className={`campaign-card__icon ${isMaster ? "campaign-card__icon--master" : ""}`}
                  aria-hidden
                >
                  {isMaster ? <Crown size={18} strokeWidth={2} /> : <Scroll size={18} strokeWidth={2} />}
                </span>
                <div>
                  <strong>{campaign.name}</strong>
                  {campaign.tone && <p className="muted">{campaign.tone}</p>}
                </div>
              </div>
              <StatusBadge label="Rol" value={campaign.role} ok={isMaster} />
              <ChevronRight className="campaign-card__chevron" size={18} aria-hidden />
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
