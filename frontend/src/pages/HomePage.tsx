import { Link } from "react-router-dom";
import { Panel, StatusBadge } from "../components/ui";
import { useHealthQuery } from "../hooks/queries/useHealthQuery";

export function HomePage() {
  const { data, isLoading, isError } = useHealthQuery();
  const status = isLoading ? "checking..." : isError ? "offline" : (data?.status ?? "offline");

  return (
    <Panel className="hero">
      <h2>Gestor de rol por turnos asistido por IA</h2>
      <p>
        Estructura inicial del monorepo: backend FastAPI, frontend PWA y pipeline RAG preparado según la
        documentación del repositorio.
      </p>
      <StatusBadge label="API" value={status} ok={status === "ok"} />
      <div className="actions">
        <Link className="button" to="/chat">
          Abrir chat de escena
        </Link>
        <Link className="button secondary" to="/master">
          Panel del Máster
        </Link>
      </div>
    </Panel>
  );
}
