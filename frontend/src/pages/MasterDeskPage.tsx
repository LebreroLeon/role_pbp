import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";
import type { MasterAssistResponse } from "../api/types";
import { queryKeys } from "../api/queryKeys";
import { RoleGate } from "../components/auth/RoleGate";
import { DESK_TAB_ICONS, SECTION_ICONS } from "../components/icons";
import { Button, ButtonLink, ConfirmDialog, ErrorBanner, Panel, PanelHeader, StatusBadge } from "../components/ui";
import { CampaignMemberList, CampaignSettingsForm, formatSceneLabel, InviteMemberForm } from "../features/campaign";
import { getChatBuffer, getSceneObjective } from "../features/scene/sceneState";
import {
  useCampaignMembersQuery,
  useCampaignQuery,
} from "../hooks/queries/useCampaignQueries";
import { useOpenSceneQuery } from "../hooks/queries/useSceneQueries";

type DeskTab = "scene" | "players" | "assist" | "settings";

const TABS: { id: DeskTab; label: string; hint: string }[] = [
  { id: "scene", label: "Escena", hint: "Estado y control" },
  { id: "players", label: "Jugadores", hint: "Mesa y invitaciones" },
  { id: "assist", label: "Asistente", hint: "Sugerencias (prototipo)" },
  { id: "settings", label: "Campaña", hint: "Datos generales" },
];

export function MasterDeskPage() {
  const { campaignId = "" } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<DeskTab>("scene");
  const [query, setQuery] = useState("¿Qué complicación encaja con la escena actual?");
  const [response, setResponse] = useState<MasterAssistResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [freezing, setFreezing] = useState(false);
  const [closing, setClosing] = useState(false);
  const [closeDialogOpen, setCloseDialogOpen] = useState(false);
  const [displayNameDraft, setDisplayNameDraft] = useState("");
  const [savingName, setSavingName] = useState(false);

  const { data: campaign } = useCampaignQuery(campaignId);
  const { data: members = [] } = useCampaignMembersQuery(campaignId);
  const { data: openScene } = useOpenSceneQuery(campaignId);

  useEffect(() => {
    setDisplayNameDraft(openScene?.display_name ?? "");
  }, [openScene?.id, openScene?.display_name]);

  async function invalidateSceneQueries() {
    await queryClient.invalidateQueries({ queryKey: queryKeys.campaigns.scenes(campaignId) });
    await queryClient.invalidateQueries({ queryKey: queryKeys.campaigns.activeScene(campaignId) });
  }

  async function handleAssist(event: FormEvent) {
    event.preventDefault();
    if (!openScene) {
      setError("No hay escena abierta. Iníciala desde Jugar.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await api.masterAssist(campaignId, openScene.id, query.trim());
      setResponse(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo consultar al asistente");
    } finally {
      setLoading(false);
    }
  }

  async function handleFreeze() {
    if (!openScene) return;
    setFreezing(true);
    setError(null);
    try {
      const next = openScene.status === "PAUSED" ? "ACTIVE" : "PAUSED";
      const updated = await api.updateSceneStatus(openScene.id, next);
      queryClient.setQueryData(queryKeys.campaigns.activeScene(campaignId), updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo cambiar el estado");
    } finally {
      setFreezing(false);
    }
  }

  async function handleCloseScene() {
    if (!openScene) return;
    setClosing(true);
    setError(null);
    try {
      await api.closeScene(openScene.id);
      queryClient.removeQueries({ queryKey: queryKeys.campaigns.activeScene(campaignId) });
      await invalidateSceneQueries();
      setCloseDialogOpen(false);
      navigate(`/campaigns/${campaignId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo cerrar la escena");
    } finally {
      setClosing(false);
    }
  }

  async function handleSaveDisplayName(event: FormEvent) {
    event.preventDefault();
    if (!openScene) return;
    setSavingName(true);
    setError(null);
    try {
      const trimmed = displayNameDraft.trim();
      const updated = await api.updateSceneDisplayName(openScene.id, trimmed || null);
      queryClient.setQueryData(queryKeys.campaigns.activeScene(campaignId), updated);
      await invalidateSceneQueries();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo guardar el nombre");
    } finally {
      setSavingName(false);
    }
  }

  return (
    <RoleGate role="MASTER">
      <div className="master-screen">
        <Panel className="master-screen__shell">
          <PanelHeader
            icon={SECTION_ICONS.mesa}
            iconTone="teal"
            title="Mesa del Máster"
            description="Herramientas de dirección: escena, jugadores y asistencia creativa."
          />

          <nav className="master-tabs">
            {TABS.map((item) => {
              const TabIcon = DESK_TAB_ICONS[item.id];
              return (
                <button
                  key={item.id}
                  type="button"
                  className={`master-tabs__btn ${tab === item.id ? "is-active" : ""}`}
                  onClick={() => setTab(item.id)}
                  title={item.hint}
                >
                  <TabIcon size={15} aria-hidden />
                  {item.label}
                </button>
              );
            })}
          </nav>

          {error && <ErrorBanner message={error} />}

          {tab === "scene" && (
            <section className="master-tab-panel">
              <h3>Escena activa</h3>
              {openScene ? (
                <>
                  <p className="muted">
                    <strong>{formatSceneLabel(openScene)}</strong>
                  </p>
                  <p className="muted">{getSceneObjective(openScene.scene_state) ?? "Sin objetivo definido"}</p>
                  <div className="status-row">
                    <StatusBadge
                      label="Estado"
                      value={
                        openScene.status === "ACTIVE"
                          ? "Activa (abierta)"
                          : openScene.status === "PAUSED"
                            ? "Pausada (congelada)"
                            : "Cerrada"
                      }
                      ok={openScene.status === "ACTIVE"}
                    />
                    <StatusBadge
                      label="Mensajes"
                      value={String(getChatBuffer(openScene.scene_state).length)}
                      ok
                    />
                  </div>
                  <form className="master-form" onSubmit={handleSaveDisplayName}>
                    <label className="field-label" htmlFor="scene-display-name">
                      Nombre de escena
                    </label>
                    <input
                      id="scene-display-name"
                      type="text"
                      value={displayNameDraft}
                      onChange={(event) => setDisplayNameDraft(event.target.value)}
                      placeholder='Ej. "La taberna del Grifo"'
                      maxLength={200}
                      disabled={savingName}
                    />
                    <Button type="submit" variant="secondary" disabled={savingName}>
                      Guardar nombre
                    </Button>
                  </form>
                  <div className="actions">
                    <ButtonLink to={`/campaigns/${campaignId}/chat`}>
                      Ir a Jugar
                    </ButtonLink>
                    <Button variant="secondary" onClick={handleFreeze} disabled={freezing}>
                      {openScene.status === "PAUSED" ? "Reanudar escena" : "Congelar escena"}
                    </Button>
                    <Button variant="secondary" onClick={() => setCloseDialogOpen(true)} disabled={closing}>
                      Cerrar escena
                    </Button>
                  </div>
                </>
              ) : (
                <p className="muted">
                  No hay escena activa. Ve a <Link to={`/campaigns/${campaignId}/chat`}>Jugar</Link> para iniciar una
                  (podrás asignar nombre al crearla).
                </p>
              )}
            </section>
          )}

          {tab === "players" && (
            <section className="master-tab-panel">
              <CampaignMemberList members={members} showEmails />
              <InviteMemberForm campaignId={campaignId} />
            </section>
          )}

          {tab === "assist" && (
            <section className="master-tab-panel">
              <p className="muted">
                Prototipo del Shadow Master: recupera contexto del chat indexado y ofrece ideas. La IA completa llegará
                en una fase posterior.
              </p>
              {!openScene && (
                <ErrorBanner message="No hay escena abierta. Inicia o reanuda una escena desde Jugar para usar el asistente." />
              )}
              <form className="master-form" onSubmit={handleAssist}>
                <textarea
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  rows={4}
                  disabled={loading || !openScene}
                />
                <Button type="submit" disabled={loading || !query.trim() || !openScene}>
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
              <CampaignSettingsForm campaignId={campaignId} campaign={campaign} />
              <div className="actions">
                <ButtonLink variant="secondary" to={`/campaigns/${campaignId}/biblioteca`}>
                  Abrir biblioteca
                </ButtonLink>
                <ButtonLink variant="secondary" to={`/campaigns/${campaignId}/mundo`}>
                  Abrir mundo
                </ButtonLink>
              </div>
            </section>
          )}
        </Panel>
      </div>

      {closeDialogOpen && (
        <ConfirmDialog
          title="Cerrar escena"
          description={
            <>
              <p>
                Se enviará todo el chat de la escena a la IA para generar un resumen narrativo en español (WorldLog).
              </p>
              <p className="muted">
                El resumen quedará en el historial de escenas y en la memoria de campaña. Esta acción no se puede
                deshacer.
              </p>
            </>
          }
          confirmLabel="Cerrar y generar resumen"
          onConfirm={handleCloseScene}
          onCancel={() => setCloseDialogOpen(false)}
          confirming={closing}
        />
      )}
    </RoleGate>
  );
}
