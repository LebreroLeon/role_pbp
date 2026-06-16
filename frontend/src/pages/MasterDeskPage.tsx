import { FormEvent, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";
import type { MasterAssistResponse } from "../api/types";
import { queryKeys } from "../api/queryKeys";
import { RoleGate } from "../components/auth/RoleGate";
import { Button, ErrorBanner, Panel, PanelHeader, StatusBadge } from "../components/ui";
import { InviteMemberForm } from "../features/campaign";
import { gameSystemLabel } from "../features/campaign/gameSystems";
import {
  useCampaignMembersQuery,
  useCampaignQuery,
} from "../hooks/queries/useCampaignQueries";
import { useActiveSceneQuery } from "../hooks/queries/useSceneQueries";

type DeskTab = "scene" | "players" | "assist" | "settings";

const TABS: { id: DeskTab; label: string; hint: string }[] = [
  { id: "scene", label: "Escena", hint: "Estado y control" },
  { id: "players", label: "Jugadores", hint: "Mesa y invitaciones" },
  { id: "assist", label: "Asistente", hint: "Sugerencias (prototipo)" },
  { id: "settings", label: "Campaña", hint: "Datos generales" },
];

export function MasterDeskPage() {
  const { campaignId = "" } = useParams();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<DeskTab>("scene");
  const [query, setQuery] = useState("¿Qué complicación encaja con la escena actual?");
  const [response, setResponse] = useState<MasterAssistResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [freezing, setFreezing] = useState(false);

  const { data: campaign } = useCampaignQuery(campaignId);
  const { data: members = [] } = useCampaignMembersQuery(campaignId);
  const { data: activeScene } = useActiveSceneQuery(campaignId);

  async function handleAssist(event: FormEvent) {
    event.preventDefault();
    if (!activeScene) {
      setError("No hay escena activa. Iníciala desde Jugar.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await api.masterAssist(campaignId, activeScene.id, query.trim());
      setResponse(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo consultar al asistente");
    } finally {
      setLoading(false);
    }
  }

  async function handleFreeze() {
    if (!activeScene) return;
    setFreezing(true);
    setError(null);
    try {
      const next = activeScene.status === "PAUSED" ? "ACTIVE" : "PAUSED";
      const updated = await api.updateSceneStatus(activeScene.id, next);
      queryClient.setQueryData(queryKeys.campaigns.activeScene(campaignId), updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo cambiar el estado");
    } finally {
      setFreezing(false);
    }
  }

  return (
    <RoleGate role="MASTER">
      <div className="master-screen">
        <Panel className="master-screen__shell">
          <PanelHeader
            title="Mesa del Máster"
            description="Herramientas de dirección: escena, jugadores y asistencia creativa."
          />

          <nav className="master-tabs">
            {TABS.map((item) => (
              <button
                key={item.id}
                type="button"
                className={`master-tabs__btn ${tab === item.id ? "is-active" : ""}`}
                onClick={() => setTab(item.id)}
                title={item.hint}
              >
                {item.label}
              </button>
            ))}
          </nav>

          {error && <ErrorBanner message={error} />}

          {tab === "scene" && (
            <section className="master-tab-panel">
              <h3>Escena activa</h3>
              {activeScene ? (
                <>
                  <p className="muted">{activeScene.scene_state.scene_objective ?? "Sin objetivo definido"}</p>
                  <div className="status-row">
                    <StatusBadge label="Estado" value={activeScene.status} ok={activeScene.status === "ACTIVE"} />
                    <StatusBadge
                      label="Mensajes"
                      value={String(activeScene.scene_state.chat_buffer.length)}
                      ok
                    />
                  </div>
                  <div className="actions">
                    <Link className="button" to={`/campaigns/${campaignId}/chat`}>
                      Ir a Jugar
                    </Link>
                    <Button variant="secondary" onClick={handleFreeze} disabled={freezing}>
                      {activeScene.status === "PAUSED" ? "Reanudar escena" : "Congelar escena"}
                    </Button>
                  </div>
                </>
              ) : (
                <p className="muted">
                  No hay escena activa. Ve a <Link to={`/campaigns/${campaignId}/chat`}>Jugar</Link> para iniciar una.
                </p>
              )}
            </section>
          )}

          {tab === "players" && (
            <section className="master-tab-panel">
              <h3>Jugadores en la mesa</h3>
              <ul className="member-list">
                {members.map((member) => (
                  <li key={member.user_id}>
                    <span>{member.display_name}</span>
                    <span className="muted">{member.email}</span>
                    <StatusBadge label="" value={member.role} ok={member.role === "MASTER"} />
                  </li>
                ))}
              </ul>
              <InviteMemberForm campaignId={campaignId} />
            </section>
          )}

          {tab === "assist" && (
            <section className="master-tab-panel">
              <p className="muted">
                Prototipo del Shadow Master: recupera contexto del chat indexado y ofrece ideas. La IA completa llegará
                en una fase posterior.
              </p>
              <form className="master-form" onSubmit={handleAssist}>
                <textarea
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  rows={4}
                  disabled={loading}
                />
                <Button type="submit" disabled={loading || !query.trim() || !activeScene}>
                  Pedir sugerencias
                </Button>
              </form>
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
          )}

          {tab === "settings" && (
            <section className="master-tab-panel">
              <h3>Datos de la campaña</h3>
              <p>
                <strong>Nombre:</strong> {campaign?.name}
              </p>
              <p>
                <strong>Sistema:</strong> {gameSystemLabel(campaign?.game_system)}
              </p>
              <p>
                <strong>Tono:</strong> {campaign?.tone ?? "Sin definir"}
              </p>
              <div className="actions">
                <Link className="button secondary" to={`/campaigns/${campaignId}/biblioteca`}>
                  Abrir biblioteca
                </Link>
                <Link className="button secondary" to={`/campaigns/${campaignId}/mundo`}>
                  Abrir mundo
                </Link>
              </div>
            </section>
          )}
        </Panel>
      </div>
    </RoleGate>
  );
}
