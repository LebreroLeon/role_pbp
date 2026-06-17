import { Link, useParams } from "react-router-dom";

import { Activity, Crown, UserPlus, Users } from "../components/icons";
import { Panel, PanelHeader, StatusBadge } from "../components/ui";
import { CampaignMemberList, CampaignSceneLog, formatSceneLabel, InviteMemberForm } from "../features/campaign";
import { gameSystemLabel } from "../features/campaign/gameSystems";
import { useCampaignMembersQuery, useCampaignQuery } from "../hooks/queries/useCampaignQueries";
import { useActiveSceneQuery } from "../hooks/queries/useSceneQueries";

export function CampaignHubPage() {
  const { campaignId = "" } = useParams();
  const base = `/campaigns/${campaignId}`;
  const { data: campaign } = useCampaignQuery(campaignId);
  const { data: members = [] } = useCampaignMembersQuery(campaignId);
  const { data: activeScene } = useActiveSceneQuery(campaignId);

  if (!campaign) return null;

  const isMaster = campaign.role === "MASTER";
  const players = members.filter((m) => m.role === "PLAYER");
  const closedScenesHint = activeScene ? formatSceneLabel(activeScene) : null;

  return (
    <div className="campaign-hub">
      <Panel>
        <PanelHeader icon={Activity} iconTone="teal" title="Estado de la partida" />
        <div className="status-row">
          <StatusBadge label="Sistema" value={gameSystemLabel(campaign.game_system)} ok />
          <StatusBadge
            label="Escena"
            value={
              activeScene
                ? activeScene.display_name
                  ? `#${activeScene.scene_number} · ${activeScene.display_name}`
                  : `#${activeScene.scene_number}`
                : "sin iniciar"
            }
            ok={activeScene?.status === "ACTIVE"}
          />
          {activeScene && (
            <StatusBadge
              label="Estado"
              value={activeScene.status === "ACTIVE" ? "activa" : activeScene.status === "PAUSED" ? "pausada" : "cerrada"}
              ok={activeScene.status === "ACTIVE"}
            />
          )}
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
        {activeScene && closedScenesHint && (
          <p className="muted hub-hint">
            Escena en curso: <strong>{closedScenesHint}</strong>
            {" · "}
            <Link to={`${base}/chat`}>Ir a Jugar</Link>
          </p>
        )}
        <CampaignSceneLog campaignId={campaignId} activeSceneId={activeScene?.id} />
      </Panel>

      <Panel>
        <PanelHeader
          icon={Users}
          iconTone="violet"
          title="Personas en la campaña"
          description={
            isMaster
              ? "Máster y jugadores con acceso a esta partida."
              : "Quién participa en la mesa."
          }
        />
        <CampaignMemberList members={members} showEmails={isMaster} />
      </Panel>

      {isMaster && (
        <Panel>
          <PanelHeader
            icon={UserPlus}
            iconTone="amber"
            title="Invitar jugador"
            description="Añade participantes por email."
          />
          <InviteMemberForm campaignId={campaignId} hideHeader />
        </Panel>
      )}

      {!isMaster && (
        <Panel>
          <PanelHeader
            icon={Crown}
            iconTone="amber"
            title="Tu rol: jugador"
            description="Escribe en el chat cuando te toque. El Máster dirige la escena; la IA le asiste en privado."
          />
        </Panel>
      )}
    </div>
  );
}
