import { Link } from "react-router-dom";

import { ErrorBanner, Panel, PanelHeader } from "../components/ui";
import { CampaignList } from "../features/campaign";
import { useCampaignsQuery } from "../hooks/queries/useCampaignQueries";

export function CampaignsPage() {
  const { data, isLoading, isError, error } = useCampaignsQuery();

  return (
    <div className="campaigns-page">
      <Panel>
        <PanelHeader
          title="Mis campañas"
          description="Partidas donde eres Máster o jugador. Crea una nueva con el asistente paso a paso."
        />
        {isLoading && <p className="muted">Cargando campañas...</p>}
        {isError && <ErrorBanner message={error instanceof Error ? error.message : "Error al cargar"} />}
        {data && <CampaignList campaigns={data} />}
        <div className="actions">
          <Link className="button" to="/campaigns/new">
            Nueva campaña
          </Link>
        </div>
      </Panel>
    </div>
  );
}
