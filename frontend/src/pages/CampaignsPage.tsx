import { ErrorBanner, Panel, PanelHeader } from "../components/ui";
import { CampaignList, CreateCampaignForm } from "../features/campaign";
import { useCampaignsQuery } from "../hooks/queries/useCampaignQueries";

export function CampaignsPage() {
  const { data, isLoading, isError, error } = useCampaignsQuery();

  return (
    <div className="campaigns-page">
      <Panel>
        <PanelHeader
          title="Mis campañas"
          description="Campañas en las que participas como Máster o jugador."
        />
        {isLoading && <p className="muted">Cargando campañas...</p>}
        {isError && <ErrorBanner message={error instanceof Error ? error.message : "Error al cargar"} />}
        {data && <CampaignList campaigns={data} />}
      </Panel>
      <CreateCampaignForm />
    </div>
  );
}
