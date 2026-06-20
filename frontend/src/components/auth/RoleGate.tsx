import { Navigate, useParams } from "react-router-dom";

import { campaignDefaultPath } from "../../features/campaign/campaignRoutes";
import { useCampaignQuery } from "../../hooks/queries/useCampaignQueries";

type RoleGateProps = {
  role: "MASTER" | "PLAYER";
  children: React.ReactNode;
};

export function RoleGate({ role, children }: RoleGateProps) {
  const { campaignId = "" } = useParams();
  const { data: campaign, isLoading, isError } = useCampaignQuery(campaignId);

  if (isLoading) {
    return <p className="muted">Cargando campaña...</p>;
  }

  if (isError || !campaign) {
    return <Navigate to="/campaigns" replace />;
  }

  if (campaign.role !== role) {
    return <Navigate to={campaignDefaultPath(campaignId, campaign.role)} replace />;
  }

  return children;
}
