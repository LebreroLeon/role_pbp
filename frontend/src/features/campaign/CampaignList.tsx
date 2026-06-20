import type { Campaign } from "../../api/types";
import { CampaignCardItem } from "./CampaignCardItem";

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
        <CampaignCardItem key={campaign.id} campaign={campaign} />
      ))}
    </ul>
  );
}
