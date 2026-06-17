import { FormEvent, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";
import type { MasterAssistResponse } from "../api/types";
import { queryKeys } from "../api/queryKeys";
import { Button, ErrorBanner, Panel, PanelHeader, StatusBadge } from "../components/ui";
import { CreateEntityForm, EntityList } from "../features/entities";
import { InviteMemberForm } from "../features/campaign";
import { getChatBuffer, getSceneObjective } from "../features/scene/sceneState";
import { useDeleteEntityMutation } from "../hooks/mutations/useEntityMutations";
import {
  useCampaignMembersQuery,
  useCampaignQuery,
} from "../hooks/queries/useCampaignQueries";
import { useEntitiesQuery } from "../hooks/queries/useEntityQueries";
import { useActiveSceneQuery } from "../hooks/queries/useSceneQueries";

type MasterTab = "scene" | "players" | "entities" | "shadow" | "settings";

const TABS: { id: MasterTab; label: string }[] = [
  { id: "scene", label: "Escena" },
  { id: "players", label: "Jugadores" },
  { id: "entities", label: "Entidades" },
  { id: "shadow", label: "Shadow Master" },
  { id: "settings", label: "Ajustes" },
];

export function MasterScreenPage() {
  const { campaignId = "" } = useParams();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<MasterTab>("scene");
  const [query, setQuery] = useState("¿Qué complicación encaja con la escena actual?");
  const [response, setResponse] = useState<MasterAssistResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [freezing, setFreezing] = useState(false);

  const { data: campaign } = useCampaignQuery(campaignId);
  const { data: members = [] } = useCampaignMembersQuery(campaignId);
  const { data: activeScene } = useActiveSceneQuery(campaignId);
  const { data: entities = [] } = useEntitiesQuery(campaignId);
  const deleteMutation = useDeleteEntityMutation(campaignId);

  async function handleAssist(event: FormEvent) {
    event.preventDefault();
    if (!activeScene) {
      setError("No hay escena activa. Iníciala desde el chat.");
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

  async function handleDeleteEntity(entityId: string) {
    setDeletingId(entityId);
    try {
      await deleteMutation.mutateAsync(entityId);
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="master-screen">
      <Panel className="master-screen__shell">
        <PanelHeader
          title="Master Screen"
          description={campaign?.name ?? "Campaña"}
          actions={
            <Link className="button secondary" to={`/campaigns/${campaignId}`}>
              Volver al hub
            </Link>
          }
        />

        <nav className="master-tabs">
          {TABS.map((item) => (
            <button
              key={item.id}
              type="button"
              className={`master-tabs__btn ${tab === item.id ? "is-active" : ""}`}
              onClick={() => setTab(item.id)}
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
                <p className="muted">{getSceneObjective(activeScene.scene_state) ?? "Sin objetivo definido"}</p>
                <div className="status-row">
                  <StatusBadge label="Estado" value={activeScene.status} ok={activeScene.status === "ACTIVE"} />
                  <StatusBadge
                    label="Mensajes"
                    value={String(getChatBuffer(activeScene.scene_state).length)}
                    ok
                  />
                </div>
                <div className="actions">
                  <Link className="button" to={`/campaigns/${campaignId}/chat`}>
                    Abrir chat
                  </Link>
                  <Button variant="secondary" onClick={handleFreeze} disabled={freezing}>
                    {activeScene.status === "PAUSED" ? "Reanudar escena" : "Congelar escena"}
                  </Button>
                </div>
              </>
            ) : (
              <p className="muted">No hay escena activa. Ve al chat para iniciar una.</p>
            )}
          </section>
        )}

        {tab === "players" && (
          <section className="master-tab-panel">
            <h3>Jugadores</h3>
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

        {tab === "entities" && (
          <section className="master-tab-panel">
            <EntityList
              entities={entities}
              isMaster
              onDelete={handleDeleteEntity}
              deletingId={deletingId}
            />
            <CreateEntityForm campaignId={campaignId} members={members} />
          </section>
        )}

        {tab === "shadow" && (
          <section className="master-tab-panel">
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
            <h3>Campaña</h3>
            <p>
              <strong>Nombre:</strong> {campaign?.name}
            </p>
            <p>
              <strong>Tono:</strong> {campaign?.tone ?? "Sin definir"}
            </p>
            <p className="muted">
              RolePBP — PBP con Shadow Master. La IA asiste solo al Máster; los jugadores nunca acceden al LLM.
            </p>
          </section>
        )}
      </Panel>
    </div>
  );
}
