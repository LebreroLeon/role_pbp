import { NavLink, Outlet, useLocation, useParams } from "react-router-dom";
import { Crown, User } from "lucide-react";

import { Breadcrumbs } from "./Breadcrumbs";
import { CAMPAIGN_NAV_ICONS } from "../icons";
import { ErrorBanner, SectionToneProvider, getToneFromPath } from "../ui";
import { gameSystemLabel } from "../../features/campaign/gameSystems";
import { useCampaignQuery } from "../../hooks/queries/useCampaignQueries";
import { useOpenSceneQuery } from "../../hooks/queries/useSceneQueries";

const MASTER_LINKS = [
  { to: "", label: "Inicio", hint: "Resumen de la campaña" },
  { to: "chat", label: "Jugar", hint: "Chat de escena" },
  { to: "ooc", label: "Fuera de personaje", hint: "OOC" },
  { to: "fichas", label: "Fichas", hint: "Todos los PJs con secretos" },
  { to: "mundo", label: "Mundo", hint: "NPCs, lugares y lore" },
  { to: "biblioteca", label: "Biblioteca", hint: "Manuales y aventuras" },
  { to: "mesa", label: "Mesa", hint: "Herramientas del Máster" },
] as const;

const PLAYER_LINKS = [
  { to: "", label: "Inicio", hint: "Resumen de la campaña" },
  { to: "chat", label: "Jugar", hint: "Chat de escena" },
  { to: "ooc", label: "Fuera de personaje", hint: "OOC" },
  { to: "ficha", label: "Mi ficha", hint: "Hoja de personaje mecánica" },
  { to: "mundo", label: "Mundo", hint: "Lo que tu PJ conoce" },
] as const;

export function CampaignLayout() {
  const { campaignId = "" } = useParams();
  const location = useLocation();
  const sectionTone = getToneFromPath(location.pathname);
  const base = `/campaigns/${campaignId}`;
  const { data: campaign, isLoading, isError, error } = useCampaignQuery(campaignId);
  const { data: openScene, isLoading: openSceneLoading } = useOpenSceneQuery(campaignId);

  if (isLoading) {
    return <p className="muted">Cargando campaña...</p>;
  }

  if (isError || !campaign) {
    return <ErrorBanner message={error instanceof Error ? error.message : "Campaña no encontrada"} />;
  }

  const isMaster = campaign.role === "MASTER";
  const links = isMaster ? MASTER_LINKS : PLAYER_LINKS;
  const sceneStatus = openScene?.status ?? "sin escena";
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
          <p className="muted campaign-shell__meta">
            {gameSystemLabel(campaign.game_system)}
            {campaign.tone ? ` · ${campaign.tone}` : ""}
            {" · "}
            Escena: {sceneStatus}
          </p>
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
          if (chatBlocked) {
            return (
              <span
                key={link.to}
                className="campaign-nav__link campaign-nav__link--disabled"
                title="Esperando al Máster"
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
            );
          }
          return (
            <NavLink
              key={link.to}
              to={link.to ? `${base}/${link.to}` : base}
              end={link.to === ""}
              className={({ isActive }) => `campaign-nav__link ${isActive ? "active" : ""}`}
              title={link.hint}
            >
              <span className="campaign-nav__icon" aria-hidden>
                <Icon size={18} strokeWidth={1.75} />
              </span>
              <span className="campaign-nav__text">
                <span className="campaign-nav__label">{link.label}</span>
                <span className="campaign-nav__hint">{link.hint}</span>
              </span>
            </NavLink>
          );
        })}
      </nav>

      <SectionToneProvider tone={sectionTone}>
        <div className="campaign-shell__content">
          <Outlet />
        </div>
      </SectionToneProvider>
    </div>
  );
}
