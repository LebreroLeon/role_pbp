import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { Panel, StatusBadge } from "../components/ui";

export function HomePage() {
  const [status, setStatus] = useState<string>("checking...");

  useEffect(() => {
    api.health()
      .then((result) => setStatus(result.status))
      .catch(() => setStatus("offline"));
  }, []);

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
