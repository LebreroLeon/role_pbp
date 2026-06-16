import { LayoutDashboard, Plus } from "../components/icons";
import { ButtonLink, ErrorBanner, Panel, PanelHeader } from "../components/ui";
import { CampaignList } from "../features/campaign";
import { useCampaignsQuery } from "../hooks/queries/useCampaignQueries";

export function CampaignsPage() {
  const { data, isLoading, isError, error } = useCampaignsQuery();

  return (
    <div className="campaigns-page">
      <Panel>
        <PanelHeader
          icon={LayoutDashboard}
          iconTone="violet"
          title="Mis campañas"
          description="Partidas donde eres Máster o jugador. Crea una nueva con el asistente paso a paso."
        />
        {isLoading && <p className="muted">Cargando campañas...</p>}
        {isError && <ErrorBanner message={error instanceof Error ? error.message : "Error al cargar"} />}
        {data && <CampaignList campaigns={data} />}
        <div className="actions">
          <ButtonLink to="/campaigns/new">
            <Plus size={16} aria-hidden />
            Nueva campaña
          </ButtonLink>
        </div>
      </Panel>
    </div>
  );
}
