import { NavLink, Outlet, useParams } from "react-router-dom";

import { Breadcrumbs } from "./Breadcrumbs";
import { ErrorBanner } from "../ui";
import { useCampaignQuery } from "../../hooks/queries/useCampaignQueries";
import { useActiveSceneQuery } from "../../hooks/queries/useSceneQueries";

const MASTER_LINKS = [
  { to: "", label: "Inicio", hint: "Resumen de la campaña" },
  { to: "chat", label: "Jugar", hint: "Chat de escena" },
  { to: "mundo", label: "Mundo", hint: "NPCs, lugares y PJ" },
  { to: "biblioteca", label: "Biblioteca", hint: "Manuales y aventuras" },
  { to: "mesa", label: "Mesa", hint: "Herramientas del Máster" },
] as const;

const PLAYER_LINKS = [
  { to: "", label: "Inicio", hint: "Resumen de la campaña" },
  { to: "chat", label: "Jugar", hint: "Chat de escena" },
  { to: "mundo", label: "Mundo", hint: "Lo que tu PJ conoce" },
] as const;

export function CampaignLayout() {
  const { campaignId = "" } = useParams();
  const base = `/campaigns/${campaignId}`;
  const { data: campaign, isLoading, isError, error } = useCampaignQuery(campaignId);
  const { data: activeScene } = useActiveSceneQuery(campaignId);

  if (isLoading) {
    return <p className="muted">Cargando campaña...</p>;
  }

  if (isError || !campaign) {
    return <ErrorBanner message={error instanceof Error ? error.message : "Campaña no encontrada"} />;
  }

  const isMaster = campaign.role === "MASTER";
  const links = isMaster ? MASTER_LINKS : PLAYER_LINKS;
  const sceneStatus = activeScene?.status ?? "sin escena";

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
            {campaign.game_system ?? "Sistema libre"}
            {campaign.tone ? ` · ${campaign.tone}` : ""}
            {" · "}
            Escena: {sceneStatus}
          </p>
        </div>
        <span className={`role-pill ${isMaster ? "role-pill--master" : "role-pill--player"}`}>
          {isMaster ? "Máster" : "Jugador"}
        </span>
      </header>

      <nav className="campaign-nav">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to ? `${base}/${link.to}` : base}
            end={link.to === ""}
            className={({ isActive }) => `campaign-nav__link ${isActive ? "active" : ""}`}
            title={link.hint}
          >
            <span className="campaign-nav__label">{link.label}</span>
            <span className="campaign-nav__hint">{link.hint}</span>
          </NavLink>
        ))}
      </nav>

      <div className="campaign-shell__content">
        <Outlet />
      </div>
    </div>
  );
}
