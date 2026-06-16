import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";

export function HomePage() {
  const [status, setStatus] = useState<string>("checking...");

  useEffect(() => {
    api.health()
      .then((result) => setStatus(result.status))
      .catch(() => setStatus("offline"));
  }, []);

  return (
    <section className="panel hero">
      <h2>Gestor de rol por turnos asistido por IA</h2>
      <p>
        Estructura inicial del monorepo: backend FastAPI, frontend PWA y pipeline RAG preparado
        según la documentación del repositorio.
      </p>
      <div className="status-row">
        <span>API</span>
        <strong className={status === "ok" ? "ok" : "warn"}>{status}</strong>
      </div>
      <div className="actions">
        <Link className="button" to="/chat">
          Abrir chat de escena
        </Link>
        <Link className="button secondary" to="/master">
          Panel del Máster
        </Link>
      </div>
    </section>
  );
}
