import { FormEvent, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api } from "../api/client";
import type { MasterAssistResponse } from "../api/types";
import { Button, ErrorBanner, Panel, PanelHeader } from "../components/ui";
import { useActiveSceneQuery } from "../hooks/queries/useSceneQueries";

export function MasterPanelPage() {
  const { campaignId = "" } = useParams();
  const { data: activeScene, isLoading: sceneLoading } = useActiveSceneQuery(campaignId);
  const [query, setQuery] = useState("¿Qué complicación encaja con la escena actual?");
  const [response, setResponse] = useState<MasterAssistResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!activeScene) {
      setError("No hay escena activa. Inicia una desde el chat primero.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const result = await api.masterAssist(campaignId, activeScene.id, query.trim());
      setResponse(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo consultar al Shadow Master");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Panel>
      <PanelHeader
        title="Panel del Máster"
        description="Canal privado de asistencia creativa con contexto RAG + estado relacional."
        actions={
          <Link className="button secondary" to={`/campaigns/${campaignId}`}>
            Volver al hub
          </Link>
        }
      />

      {sceneLoading && <p className="muted">Buscando escena activa...</p>}
      {!sceneLoading && !activeScene && (
        <ErrorBanner message="No hay escena activa. Ve al chat e inicia una escena antes de pedir asistencia." />
      )}

      <form className="master-form" onSubmit={handleSubmit}>
        <textarea value={query} onChange={(event) => setQuery(event.target.value)} rows={4} disabled={loading} />
        <Button type="submit" disabled={loading || !query.trim() || !activeScene}>
          Pedir sugerencias
        </Button>
      </form>

      {error && <ErrorBanner message={error} />}

      {response && (
        <div className="master-result">
          <h3>Contexto recuperado</h3>
          <p>{response.context_summary}</p>
          <h3>Sugerencias</h3>
          <ul>
            {response.suggestions.map((suggestion) => (
              <li key={suggestion}>{suggestion}</li>
            ))}
          </ul>
          <p className="muted">{response.note}</p>
        </div>
      )}
    </Panel>
  );
}
