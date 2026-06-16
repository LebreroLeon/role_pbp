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
      <h2>Rol por turnos, claro y en el bolsillo</h2>
      <p>
        RolePBP organiza tu campaña en secciones sencillas: <strong>Jugar</strong> (chat),{" "}
        <strong>Mundo</strong> (NPCs y lugares), <strong>Biblioteca</strong> (manuales y aventuras) y{" "}
        <strong>Mesa del Máster</strong> (dirección de partida).
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
