import { NavLink, Outlet, useLocation, useParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { Crown, User } from "lucide-react";

import { Breadcrumbs } from "./Breadcrumbs";
import { CAMPAIGN_NAV_ICONS } from "../icons";
import { ErrorBanner, SectionToneProvider, Tooltip, UnreadBadge, adjustCountsForActiveTab, getToneFromPath } from "../ui";
import { CampaignStatusBadges } from "../../features/campaign/CampaignStatusBadges";
import { useCampaignQuery } from "../../hooks/queries/useCampaignQueries";
import { useOpenSceneQuery } from "../../hooks/queries/useSceneQueries";
import { useUnreadCountsQuery } from "../../hooks/queries/useUnreadCountsQuery";
import { queryKeys } from "../../api/queryKeys";
import { CampaignWsProvider } from "../../providers/CampaignWsContext";

const MASTER_LINKS = [
  { to: "chat", label: "Jugar", hint: "Chat de escena" },
  { to: "ooc", label: "Fuera de personaje", hint: "OOC" },
  { to: "fichas", label: "Fichas", hint: "Todos los PJs con secretos" },
  { to: "mundo", label: "Mundo", hint: "NPCs, lugares y lore" },
  { to: "biblioteca", label: "Biblioteca", hint: "Manuales y aventuras" },
  { to: "mesa", label: "Mesa", hint: "Herramientas del Máster" },
] as const;

const PLAYER_LINKS = [
  { to: "chat", label: "Jugar", hint: "Chat de escena" },
  { to: "ooc", label: "Fuera de personaje", hint: "OOC" },
  { to: "ficha", label: "Mi ficha", hint: "Hoja de personaje mecánica" },
  { to: "mundo", label: "Mundo", hint: "Lo que tu PJ conoce" },
] as const;

const UNREAD_BADGE_CHANNELS = {
  chat: "play",
  ooc: "ooc",
} as const satisfies Record<string, keyof import("../../api/types").UnreadCounts>;

export function CampaignLayout() {
  const { campaignId = "" } = useParams();
  const location = useLocation();
  const queryClient = useQueryClient();
  const sectionTone = getToneFromPath(location.pathname);
  const base = `/campaigns/${campaignId}`;
  const { data: campaign, isLoading, isError, error } = useCampaignQuery(campaignId);
  const { data: openScene, isLoading: openSceneLoading } = useOpenSceneQuery(campaignId);
  const { data: unreadCounts } = useUnreadCountsQuery(campaignId);
  const displayCounts = adjustCountsForActiveTab(
    unreadCounts ?? { play: 0, ooc: 0 },
    location.pathname,
  );

  if (isLoading) {
    return <p className="muted">Cargando campaña...</p>;
  }

  if (isError || !campaign) {
    return <ErrorBanner message={error instanceof Error ? error.message : "Campaña no encontrada"} />;
  }

  const isMaster = campaign.role === "MASTER";
  const links = isMaster ? MASTER_LINKS : PLAYER_LINKS;
  const playerChatBlocked = !isMaster && !openSceneLoading && !openScene;
  const RoleIcon = isMaster ? Crown : User;

  return (
    <div className="campaign-shell">
      <Breadcrumbs
        items={[
          { label: "Campañas", to: "/campaigns" },
          { label: campaign.name },
        ]}
      />

      <header className="campaign-shell__header">
        <div>
          <h2 className="campaign-shell__title">{campaign.name}</h2>
          {isMaster && campaign.tone && <p className="muted campaign-shell__meta">{campaign.tone}</p>}
          <CampaignStatusBadges
            campaign={campaign}
            openScene={openScene}
            showSceneCounts
            className="campaign-shell__badges"
          />
        </div>
        <span className={`role-pill ${isMaster ? "role-pill--master" : "role-pill--player"}`}>
          <RoleIcon size={14} aria-hidden />
          {isMaster ? "Máster" : "Jugador"}
        </span>
      </header>

      <nav className="campaign-nav">
        {links.map((link) => {
          const Icon = CAMPAIGN_NAV_ICONS[link.to as keyof typeof CAMPAIGN_NAV_ICONS];
          const chatBlocked = link.to === "chat" && playerChatBlocked;
          const unreadKey = UNREAD_BADGE_CHANNELS[link.to as keyof typeof UNREAD_BADGE_CHANNELS];
          const unreadCount = unreadKey ? displayCounts[unreadKey] : 0;
          if (chatBlocked) {
            return (
              <Tooltip key={link.to} content="Esperando al Máster">
                <span
                  className="campaign-nav__link campaign-nav__link--disabled"
                  aria-disabled="true"
                >
                <span className="campaign-nav__icon" aria-hidden>
                  <Icon size={18} strokeWidth={1.75} />
                </span>
                <span className="campaign-nav__text">
                  <span className="campaign-nav__label">{link.label}</span>
                  <span className="campaign-nav__hint">Esperando al Máster</span>
                </span>
                </span>
              </Tooltip>
            );
          }
          return (
            <Tooltip key={link.to} content={link.hint}>
              <NavLink
                to={`${base}/${link.to}`}
                className={({ isActive }) => `campaign-nav__link ${isActive ? "active" : ""}`}
              >
              <span className="campaign-nav__icon" aria-hidden>
                <Icon size={18} strokeWidth={1.75} />
              </span>
              <span className="campaign-nav__text">
                <span className="campaign-nav__label-row">
                  <span className="campaign-nav__label">{link.label}</span>
                  <UnreadBadge count={unreadCount} label={`${unreadCount} sin leer en ${link.label}`} />
                </span>
                <span className="campaign-nav__hint">{link.hint}</span>
              </span>
            </NavLink>
            </Tooltip>
          );
        })}
      </nav>

      <SectionToneProvider tone={sectionTone}>
        <CampaignWsProvider
          campaignId={campaignId}
          onUnreadCounts={(counts) => {
            queryClient.setQueryData(queryKeys.campaigns.unreadCounts(campaignId), counts);
          }}
        >
          <div className="campaign-shell__content">
            <Outlet />
          </div>
        </CampaignWsProvider>
      </SectionToneProvider>
    </div>
  );
}
