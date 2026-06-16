import { SECTION_ICONS } from "../components/icons";
import { ButtonLink, Panel, StatusBadge } from "../components/ui";
import { useHealthQuery } from "../hooks/queries/useHealthQuery";
import { useAuthStore } from "../stores/authStore";

const FEATURES = [
  { icon: SECTION_ICONS.chat, label: "Jugar", hint: "Chat en tiempo real" },
  { icon: SECTION_ICONS.mundo, label: "Mundo", hint: "NPCs y lugares" },
  { icon: SECTION_ICONS.biblioteca, label: "Biblioteca", hint: "Manuales y notas" },
  { icon: SECTION_ICONS.mesa, label: "Mesa del Máster", hint: "Dirección de partida" },
] as const;

export function HomePage() {
  const { data, isLoading, isError } = useHealthQuery();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated());
  const status = isLoading ? "checking..." : isError ? "offline" : (data?.status ?? "offline");

  return (
    <Panel className="hero">
      <p className="eyebrow">Play-by-post moderno</p>
      <h2>Rol por turnos, claro y en el bolsillo</h2>
      <p>
        RolePBP organiza tu campaña en secciones sencillas. Cada área tiene un propósito claro para que
        jugadores y Máster sepan siempre dónde ir.
      </p>

      <div className="hero-features">
        {FEATURES.map(({ icon: Icon, label, hint }) => (
          <div key={label} className="hero-feature">
            <Icon size={18} strokeWidth={2} aria-hidden />
            <span>
              <strong>{label}</strong>
              <span className="hero-feature__hint"> · {hint}</span>
            </span>
          </div>
        ))}
      </div>

      <StatusBadge label="API" value={status} ok={status === "ok"} />
      <div className="actions">
        {isAuthenticated ? (
          <ButtonLink to="/campaigns">Mis campañas</ButtonLink>
        ) : (
          <>
            <ButtonLink to="/register">Crear cuenta</ButtonLink>
            <ButtonLink variant="secondary" to="/login">
              Iniciar sesión
            </ButtonLink>
          </>
        )}
      </div>
    </Panel>
  );
}
