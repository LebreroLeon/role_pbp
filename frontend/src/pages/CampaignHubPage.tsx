import { Link, useParams } from "react-router-dom";

import { Panel, PanelHeader, StatusBadge } from "../components/ui";
import { CampaignNavCard } from "../components/navigation/CampaignNavCard";
import { InviteMemberForm } from "../features/campaign";
import { gameSystemLabel } from "../features/campaign/gameSystems";
import { useCampaignMembersQuery, useCampaignQuery } from "../hooks/queries/useCampaignQueries";
import { useActiveSceneQuery } from "../hooks/queries/useSceneQueries";
import { useEntitiesQuery } from "../hooks/queries/useEntityQueries";
import { useDocumentsQuery } from "../hooks/queries/useDocumentQueries";

export function CampaignHubPage() {
  const { campaignId = "" } = useParams();
  const base = `/campaigns/${campaignId}`;
  const { data: campaign } = useCampaignQuery(campaignId);
  const { data: members = [] } = useCampaignMembersQuery(campaignId);
  const { data: activeScene } = useActiveSceneQuery(campaignId);
  const { data: entities = [] } = useEntitiesQuery(campaignId);
  const { data: documents = [] } = useDocumentsQuery(campaignId);

  if (!campaign) return null;

  const isMaster = campaign.role === "MASTER";
  const players = members.filter((m) => m.role === "PLAYER");

  return (
    <div className="campaign-hub">
      <Panel>
        <PanelHeader
          title="¿Qué quieres hacer?"
          description="Elige una sección. Cada área tiene un propósito claro en tu partida PBP."
        />
        <div className="nav-card-grid">
          <CampaignNavCard
            accent="primary"
            title="Jugar"
            description="Chat de escena en tiempo real: diálogo, acciones, contexto y tiradas."
            to={`${base}/chat`}
          />
          <CampaignNavCard
            title="Mundo"
            description={`NPCs, lugares y personajes (${entities.length} elementos).`}
            to={`${base}/mundo`}
          />
          {isMaster && (
            <>
              <CampaignNavCard
                title="Biblioteca"
                description={`Manuales, aventuras y notas (${documents.length} archivos).`}
                to={`${base}/biblioteca`}
              />
              <CampaignNavCard
                title="Mesa del Máster"
                description="Control de escena, jugadores y herramientas de dirección."
                to={`${base}/mesa`}
              />
            </>
          )}
        </div>
      </Panel>

      <Panel>
        <PanelHeader title="Estado de la partida" />
        <div className="status-row">
          <StatusBadge label="Sistema" value={gameSystemLabel(campaign.game_system)} ok />
          <StatusBadge
            label="Escena"
            value={activeScene ? activeScene.status : "sin iniciar"}
            ok={activeScene?.status === "ACTIVE"}
          />
          <StatusBadge label="Jugadores" value={String(players.length)} ok={players.length > 0} />
        </div>
        {!activeScene && (
          <p className="muted hub-hint">
            {isMaster ? (
              <>
                Aún no hay escena activa. Ve a <Link to={`${base}/chat`}>Jugar</Link> para iniciarla.
              </>
            ) : (
              "El Máster aún no ha iniciado la escena. Cuando lo haga, aparecerá aquí."
            )}
          </p>
        )}
      </Panel>

      {isMaster && (
        <Panel>
          <PanelHeader title="Invitar jugador" description="Añade participantes por email." />
          <InviteMemberForm campaignId={campaignId} />
        </Panel>
      )}

      {!isMaster && (
        <Panel>
          <PanelHeader
            title="Tu rol: jugador"
            description="Escribe en el chat cuando te toque. El Máster dirige la escena; la IA le asiste en privado."
          />
        </Panel>
      )}
    </div>
  );
}
