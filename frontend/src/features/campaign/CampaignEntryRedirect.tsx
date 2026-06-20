import { Navigate, useParams } from "react-router-dom";

import { useCampaignQuery } from "../../hooks/queries/useCampaignQueries";
import { useOpenSceneQuery } from "../../hooks/queries/useSceneQueries";
import { campaignDefaultPath } from "./campaignRoutes";

export function CampaignEntryRedirect() {
  const { campaignId = "" } = useParams();
  const { data: campaign, isLoading } = useCampaignQuery(campaignId);
  const { data: openScene, isLoading: sceneLoading } = useOpenSceneQuery(campaignId);

  if (isLoading || sceneLoading) {
    return <p className="muted">Cargando campaña...</p>;
  }

  if (!campaign) {
    return <Navigate to="/campaigns" replace />;
  }

  return <Navigate to={campaignDefaultPath(campaignId, campaign.role, openScene)} replace />;
}
