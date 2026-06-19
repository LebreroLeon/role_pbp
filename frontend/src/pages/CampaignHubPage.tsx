import { Link, useParams } from "react-router-dom";

import { Activity, CheckCircle2, Circle, Crown, UserPlus, Users } from "../components/icons";
import { Panel, PanelHeader, StatusBadge } from "../components/ui";
import { CampaignMemberList, CampaignSceneLog, formatSceneLabel, InviteMemberForm } from "../features/campaign";
import { gameSystemLabel } from "../features/campaign/gameSystems";
import { useCampaignMembersQuery, useCampaignQuery } from "../hooks/queries/useCampaignQueries";
import { useEntitiesQuery } from "../hooks/queries/useEntityQueries";
import { useOpenSceneQuery } from "../hooks/queries/useSceneQueries";
import { useAuthStore } from "../stores/authStore";

export function CampaignHubPage() {
  const { campaignId = "" } = useParams();
  const base = `/campaigns/${campaignId}`;
  const currentUserId = useAuthStore((state) => state.user?.id ?? "");
  const { data: campaign } = useCampaignQuery(campaignId);
  const { data: members = [] } = useCampaignMembersQuery(campaignId);
  const { data: openScene } = useOpenSceneQuery(campaignId);
  const { data: entities = [] } = useEntitiesQuery(campaignId);

  if (!campaign) return null;

  const isMaster = campaign.role === "MASTER";
  const players = members.filter((m) => m.role === "PLAYER");
  const closedScenesHint = openScene ? formatSceneLabel(openScene) : null;
  const playerSheet = entities.find(
    (entity) =>
      entity.entity_type === "PC" &&
      (entity.document.player_binding as { user_id?: string } | undefined)?.user_id === currentUserId,
  );
  const hasPlayerSheet = Boolean(playerSheet);
  const hasActiveScene = openScene?.status === "ACTIVE";
  const onboardingComplete = hasPlayerSheet && hasActiveScene;

  return (
    <div className="campaign-hub">
      <Panel>
        <PanelHeader icon={Activity} iconTone="teal" title="Estado de la partida" />
        <div className="status-row">
          <StatusBadge label="Sistema" value={gameSystemLabel(campaign.game_system)} ok />
          <StatusBadge
            label="Escena"
            value={
              openScene
                ? openScene.display_name
                  ? `#${openScene.scene_number} · ${openScene.display_name}`
                  : `#${openScene.scene_number}`
                : "sin iniciar"
            }
            ok={openScene?.status === "ACTIVE"}
          />
          {openScene && (
            <StatusBadge
              label="Estado"
              value={openScene.status === "ACTIVE" ? "Activa (abierta)" : openScene.status === "PAUSED" ? "Pausada (congelada)" : "Cerrada"}
              ok={openScene.status === "ACTIVE"}
            />
          )}
          <StatusBadge label="Jugadores" value={String(players.length)} ok={players.length > 0} />
        </div>
        {!openScene && (
          <p className="muted hub-hint">
            {isMaster ? (
              <>
                Aún no hay escena activa. Ve a <Link to={`${base}/chat`}>Jugar</Link> para iniciarla.
              </>
            ) : (
              "Esperando al Máster. El Máster debe iniciar la siguiente escena antes de que puedas entrar al chat."
            )}
          </p>
        )}
        {openScene && closedScenesHint && (
          <p className="muted hub-hint">
            Escena en curso: <strong>{closedScenesHint}</strong>
            {" · "}
            <Link to={`${base}/chat`}>Ir a Jugar</Link>
          </p>
        )}
        <CampaignSceneLog campaignId={campaignId} activeSceneId={openScene?.id} isMaster={isMaster} />
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
            description="Completa estos pasos para unirte a la partida."
          />
          <ul className="player-onboarding">
            <li className={hasPlayerSheet ? "is-done" : ""}>
              {hasPlayerSheet ? <CheckCircle2 aria-hidden /> : <Circle aria-hidden />}
              <span>
                {hasPlayerSheet ? "Ficha creada" : "Crea tu ficha de personaje"}
                {!hasPlayerSheet && (
                  <>
                    {" — "}
                    <Link to={`${base}/ficha`}>Ir a Ficha</Link>
                  </>
                )}
              </span>
            </li>
            <li className={hasActiveScene ? "is-done" : ""}>
              {hasActiveScene ? <CheckCircle2 aria-hidden /> : <Circle aria-hidden />}
              <span>
                {hasActiveScene ? "Escena activa" : "Espera a que el Máster inicie la escena"}
                {hasActiveScene && (
                  <>
                    {" — "}
                    <Link to={`${base}/chat`}>Ir a Jugar</Link>
                  </>
                )}
              </span>
            </li>
            <li>
              <Circle aria-hidden className="onboarding-optional" />
              <span>
                Coordínate fuera de escena en <Link to={`${base}/ooc`}>Chat OOC</Link>
              </span>
            </li>
          </ul>
          {onboardingComplete && (
            <p className="muted hub-hint">
              Todo listo. Entra al <Link to={`${base}/chat`}>chat de escena</Link> o revisa el{" "}
              <Link to={`${base}/ooc`}>OOC</Link>.
            </p>
          )}
        </Panel>
      )}
    </div>
  );
}
