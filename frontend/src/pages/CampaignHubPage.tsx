import { Link, useParams } from "react-router-dom";

import { Button, ErrorBanner, Panel, PanelHeader, StatusBadge } from "../components/ui";
import { InviteMemberForm } from "../features/campaign";
import { useCampaignMembersQuery, useCampaignQuery } from "../hooks/queries/useCampaignQueries";

export function CampaignHubPage() {
  const { campaignId = "" } = useParams();
  const { data: campaign, isLoading, isError, error } = useCampaignQuery(campaignId);
  const { data: members } = useCampaignMembersQuery(campaignId);

  if (isLoading) {
    return <p className="muted">Cargando campaña...</p>;
  }

  if (isError || !campaign) {
    return <ErrorBanner message={error instanceof Error ? error.message : "Campaña no encontrada"} />;
  }

  const isMaster = campaign.role === "MASTER";

  return (
    <div className="campaign-hub">
      <Panel>
        <PanelHeader
          title={campaign.name}
          description={campaign.tone ?? "Sin tono definido"}
          actions={<StatusBadge label="Tu rol" value={campaign.role} ok={isMaster} />}
        />

        <div className="actions">
          <Link className="button" to={`/campaigns/${campaignId}/chat`}>
            Ir al chat de escena
          </Link>
          <Link className="button secondary" to={`/campaigns/${campaignId}/entities`}>
            Entidades
          </Link>
          {isMaster && (
            <Link className="button secondary" to={`/campaigns/${campaignId}/master`}>
              Master Screen
            </Link>
          )}
        </div>
      </Panel>

      <Panel>
        <PanelHeader title="Miembros" description={`${members?.length ?? 0} participantes`} />
        {members && members.length > 0 ? (
          <ul className="member-list">
            {members.map((member) => (
              <li key={member.user_id}>
                <span>{member.display_name}</span>
                <span className="muted">{member.email}</span>
                <StatusBadge label="" value={member.role} ok={member.role === "MASTER"} />
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">Sin miembros listados.</p>
        )}
      </Panel>

      {isMaster && <InviteMemberForm campaignId={campaignId} />}

      {!isMaster && (
        <Panel>
          <PanelHeader
            title="Vista de jugador"
            description="Participa en el chat de escena. El asistente IA solo está disponible para el Máster."
          />
          <Link to={`/campaigns/${campaignId}/chat`}>
            <Button>Abrir chat</Button>
          </Link>
        </Panel>
      )}
    </div>
  );
}
