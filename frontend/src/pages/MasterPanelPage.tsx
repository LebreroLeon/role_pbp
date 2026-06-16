import { FormEvent, useState } from "react";
import { api, MasterAssistResponse } from "../api/client";

const DEFAULT_CAMPAIGN = "00000000-0000-4000-8000-000000000001";
const DEFAULT_SCENE = "00000000-0000-4000-8000-000000000002";

export function MasterPanelPage() {
  const [query, setQuery] = useState("¿Qué complicación encaja con la escena actual?");
  const [response, setResponse] = useState<MasterAssistResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const result = await api.masterAssist(DEFAULT_CAMPAIGN, DEFAULT_SCENE, query.trim());
      setResponse(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo consultar al Shadow Master");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel">
      <header className="panel-header">
        <div>
          <h2>Panel del Máster</h2>
          <p>Canal privado de asistencia creativa con contexto RAG + estado relacional.</p>
        </div>
      </header>

      <form className="master-form" onSubmit={handleSubmit}>
        <textarea
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          rows={4}
          disabled={loading}
        />
        <button className="button" type="submit" disabled={loading || !query.trim()}>
          Pedir sugerencias
        </button>
      </form>

      {error && <p className="error">{error}</p>}

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
    </section>
  );
}
