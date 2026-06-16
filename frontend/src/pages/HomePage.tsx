import { Link } from "react-router-dom";

import { Panel, StatusBadge } from "../components/ui";
import { useHealthQuery } from "../hooks/queries/useHealthQuery";
import { useAuthStore } from "../stores/authStore";

export function HomePage() {
  const { data, isLoading, isError } = useHealthQuery();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated());
  const status = isLoading ? "checking..." : isError ? "offline" : (data?.status ?? "offline");

  return (
    <Panel className="hero">
      <h2>Gestor de rol por turnos asistido por IA</h2>
      <p>
        Hub play-by-post con patrón Shadow Master: la IA asiste solo al Máster. Regístrate, crea una campaña e
        invita jugadores.
      </p>
      <StatusBadge label="API" value={status} ok={status === "ok"} />
      <div className="actions">
        {isAuthenticated ? (
          <Link className="button" to="/campaigns">
            Mis campañas
          </Link>
        ) : (
          <>
            <Link className="button" to="/register">
              Crear cuenta
            </Link>
            <Link className="button secondary" to="/login">
              Iniciar sesión
            </Link>
          </>
        )}
      </div>
    </Panel>
  );
}
