import { FormEvent, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api } from "../api/client";
import type { MasterAssistResponse } from "../api/types";
import { Button, ErrorBanner, Panel, PanelHeader } from "../components/ui";

export function MasterPanelPage() {
  const { campaignId = "" } = useParams();
  const [sceneId, setSceneId] = useState<string | null>(null);
  const [query, setQuery] = useState("¿Qué complicación encaja con la escena actual?");
  const [response, setResponse] = useState<MasterAssistResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function ensureSceneId(): Promise<string> {
    if (sceneId) return sceneId;
    const scene = await api.createScene(campaignId, "Escena para asistencia del Máster");
    setSceneId(scene.id);
    return scene.id;
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const activeSceneId = await ensureSceneId();
      const result = await api.masterAssist(campaignId, activeSceneId, query.trim());
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

      <form className="master-form" onSubmit={handleSubmit}>
        <textarea value={query} onChange={(event) => setQuery(event.target.value)} rows={4} disabled={loading} />
        <Button type="submit" disabled={loading || !query.trim()}>
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
