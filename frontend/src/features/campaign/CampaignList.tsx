import { Link } from "react-router-dom";

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
      {campaigns.map((campaign) => (
        <li key={campaign.id}>
          <Link to={`/campaigns/${campaign.id}`} className="campaign-card">
            <div>
              <strong>{campaign.name}</strong>
              {campaign.tone && <p className="muted">{campaign.tone}</p>}
            </div>
            <StatusBadge label="Rol" value={campaign.role} ok={campaign.role === "MASTER"} />
          </Link>
        </li>
      ))}
    </ul>
  );
}
