import { FormEvent, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { Send } from "lucide-react";

import { api } from "../api/client";
import type { MasterAssistMode, MasterAssistResponse } from "../api/types";
import { queryKeys } from "../api/queryKeys";
import { RoleGate } from "../components/auth/RoleGate";
import { DESK_TAB_ICONS, SECTION_ICONS } from "../components/icons";
import { Button, ErrorBanner, Panel, PanelHeader, Toast, Tooltip } from "../components/ui";
import { CampaignSettingsForm, campaignDefaultPath } from "../features/campaign";
import { PreparedScenesPanel, NextSceneModal } from "../features/scene";
import { useCampaignQuery } from "../hooks/queries/useCampaignQueries";
import { useOpenSceneQuery } from "../hooks/queries/useSceneQueries";

const NARRATOR_SPEAKER = {
  speaker_type: "NARRATOR" as const,
  speaker_display_name: "Máster / Narrador",
};

type DeskTab = "escenas" | "assist" | "settings";

type ShadowMasterMode = MasterAssistMode;

const SHADOW_MASTER_MODES: {
  id: ShadowMasterMode;
  label: string;
  hint: string;
  placeholder: string;
  defaultQuery: string;
}[] = [
  {
    id: "narrative",
    label: "Narrativa",
    hint: "Prosa lista para publicar en el chat",
    placeholder: "Ej. ¿Cómo podría empezar o continuar la narración de la escena?",
    defaultQuery: "¿Cómo podría continuar la narración en la escena actual?",
  },
  {
    id: "rules",
    label: "Manual",
    hint: "Reglas, precios y mecánicas del sistema",
    placeholder: "Ej. ¿Cuánto vale una armadura de placas? ¿Qué competencias tiene el arquero arcano?",
    defaultQuery: "¿Cuánto vale en el mercado una armadura pesada completa?",
  },
  {
    id: "campaign",
    label: "Escena y campaña",
    hint: "Lore, contexto, entidades y memoria de campaña",
    placeholder: "Ej. ¿Qué pasó la última vez aquí? ¿Quién conoce a este NPC?",
    defaultQuery: "¿Qué complicación encaja con la escena actual?",
  },
];

const SHADOW_MASTER_MODE_META: Record<
  ShadowMasterMode | "creative",
  { summaryTitle: string; suggestionsTitle: string; hint?: string }
> = {
  narrative: {
    summaryTitle: "Análisis",
    suggestionsTitle: "Sugerencias narrativas",
    hint: "Edita antes de enviar. El texto se publicará en la escena activa tal como lo dejes.",
  },
  rules: {
    summaryTitle: "Respuesta",
    suggestionsTitle: "Detalle",
  },
  campaign: {
    summaryTitle: "Contexto",
    suggestionsTitle: "Puntos útiles",
  },
  creative: {
    summaryTitle: "Análisis",
    suggestionsTitle: "Ideas",
  },
};

const TABS: { id: DeskTab; label: string; hint: string }[] = [
  { id: "escenas", label: "Escenas", hint: "Activa, preparadas e historial" },
  { id: "assist", label: "Shadow Master", hint: "Reglas, precios e ideas narrativas" },
  { id: "settings", label: "Campaña", hint: "Datos generales y jugadores" },
];

export function MasterDeskPage() {
  const { campaignId = "" } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<DeskTab>("escenas");
  const [assistMode, setAssistMode] = useState<ShadowMasterMode>("campaign");
  const [query, setQuery] = useState(SHADOW_MASTER_MODES.find((m) => m.id === "campaign")!.defaultQuery);
  const [response, setResponse] = useState<MasterAssistResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [nextSceneOpen, setNextSceneOpen] = useState(false);
  const [preparedScenes, setPreparedScenes] = useState<import("../api/types").ScenePickerItem[]>([]);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [sendingSuggestionKey, setSendingSuggestionKey] = useState<string | null>(null);
  const [narrativeDrafts, setNarrativeDrafts] = useState<string[]>([]);

  const narrativeSuggestions = useMemo(() => {
    if (!response || assistMode !== "narrative") return [];
    if (response.suggestions.length > 0) return response.suggestions;
    if (response.context_summary.trim()) return [response.context_summary.trim()];
    return [];
  }, [response, assistMode]);

  useEffect(() => {
    setNarrativeDrafts(narrativeSuggestions);
  }, [narrativeSuggestions]);

  const { data: campaign } = useCampaignQuery(campaignId);
  const { data: openScene } = useOpenSceneQuery(campaignId);

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
      const result = await api.masterAssist(campaignId, openScene.id, query.trim(), assistMode);
      setResponse(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo consultar al asistente");
    } finally {
      setLoading(false);
    }
  }

  async function handleSendToScene(text: string, suggestionKey: string) {
    if (!openScene) {
      setToastMessage("No hay escena abierta para publicar.");
      return;
    }
    if (openScene.status !== "ACTIVE" && openScene.status !== "PAUSED") {
      setToastMessage("La escena debe estar activa o pausada para publicar.");
      return;
    }

    setSendingSuggestionKey(suggestionKey);
    try {
      const updated = await api.postMessage(openScene.id, text, "ACTION", NARRATOR_SPEAKER);
      queryClient.setQueryData(queryKeys.campaigns.activeScene(campaignId), updated);
      await queryClient.invalidateQueries({ queryKey: queryKeys.campaigns.scenes(campaignId) });
      setToastMessage("Narración enviada a la escena.");
    } catch (err) {
      setToastMessage(err instanceof Error ? err.message : "No se pudo enviar a la escena.");
    } finally {
      setSendingSuggestionKey(null);
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
            description="Herramientas de dirección: escena, campaña y asistencia creativa."
          />

          <nav className="master-tabs">
            {TABS.map((item) => {
              const TabIcon = DESK_TAB_ICONS[item.id];
              return (
                <Tooltip key={item.id} content={item.hint}>
                  <button
                    type="button"
                    className={`master-tabs__btn ${tab === item.id ? "is-active" : ""}`}
                    onClick={() => setTab(item.id)}
                    aria-label={item.hint}
                  >
                    <TabIcon size={15} aria-hidden />
                    {item.label}
                  </button>
                </Tooltip>
              );
            })}
          </nav>

          {error && <ErrorBanner message={error} />}

          {tab === "escenas" && (
            <section className="master-tab-panel master-scenes-panel">
              <PreparedScenesPanel
                campaignId={campaignId}
                onSceneClosed={(scenes) => {
                  setPreparedScenes(scenes);
                  setNextSceneOpen(true);
                }}
              />
            </section>
          )}

          {tab === "assist" && (
            <section className="master-tab-panel">
              <p className="muted">
                Elige un modo: narrativa para prosa publicable, manual para reglas del sistema, o escena y campaña
                para lore, contexto y memoria indexada.
              </p>
              {!openScene && (
                <ErrorBanner message="No hay escena abierta. Inicia o reanuda una escena desde Jugar para usar el Shadow Master." />
              )}
              <div className="shadow-master-modes" role="group" aria-label="Modo del Shadow Master">
                {SHADOW_MASTER_MODES.map((mode) => (
                  <Tooltip key={mode.id} content={mode.hint}>
                    <button
                      type="button"
                      className={`shadow-master-modes__btn ${assistMode === mode.id ? "is-active" : ""}`}
                      onClick={() => {
                        setAssistMode(mode.id);
                        setQuery(mode.defaultQuery);
                        setResponse(null);
                      }}
                      aria-label={mode.hint}
                      disabled={loading}
                    >
                      {mode.label}
                    </button>
                  </Tooltip>
                ))}
              </div>
              <form className="master-form" onSubmit={handleAssist}>
                <label className="field-label" htmlFor="shadow-master-query">
                  Consulta al Shadow Master — {SHADOW_MASTER_MODES.find((m) => m.id === assistMode)?.label}
                </label>
                <textarea
                  id="shadow-master-query"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  rows={4}
                  placeholder={SHADOW_MASTER_MODES.find((m) => m.id === assistMode)?.placeholder}
                  disabled={loading || !openScene}
                />
                <Button type="submit" disabled={loading || !query.trim() || !openScene}>
                  {loading ? "Consultando…" : "Consultar"}
                </Button>
              </form>
              {response && (() => {
                const displayKind = assistMode;
                const meta = SHADOW_MASTER_MODE_META[displayKind] ?? SHADOW_MASTER_MODE_META.campaign;
                const isNarrative = assistMode === "narrative";
                return (
                <div className="master-result">
                  <section className="master-result__section">
                    <h3>{meta.summaryTitle}</h3>
                    <p>{response.context_summary}</p>
                  </section>

                  {narrativeSuggestions.length > 0 && isNarrative && (
                    <section className="master-result__section master-result__narrative">
                      <h3>{meta.suggestionsTitle}</h3>
                      {meta.hint && <p className="muted master-result__hint">{meta.hint}</p>}
                      {response.suggestions.length === 0 && (
                        <p className="muted master-result__hint">
                          No llegaron sugerencias separadas; puedes enviar el análisis como narración o reformular la
                          consulta.
                        </p>
                      )}
                      <ul className="master-narrative-suggestions">
                        {narrativeDrafts.map((draft, index) => {
                          const suggestionKey = `narrative-${index}`;
                          const sending = sendingSuggestionKey === suggestionKey;
                          const trimmedDraft = draft.trim();
                          return (
                            <li key={suggestionKey} className="master-narrative-suggestion">
                              <textarea
                                id={`narrative-suggestion-${index}`}
                                className="master-narrative-suggestion__text"
                                aria-label={`Sugerencia narrativa ${index + 1}`}
                                value={draft}
                                onChange={(event) =>
                                  setNarrativeDrafts((prev) =>
                                    prev.map((item, itemIndex) =>
                                      itemIndex === index ? event.target.value : item,
                                    ),
                                  )
                                }
                                rows={4}
                                disabled={sending}
                              />
                              <Button
                                type="button"
                                variant="secondary"
                                className="master-narrative-suggestion__send"
                                disabled={!openScene || sending || !trimmedDraft}
                                onClick={() => handleSendToScene(trimmedDraft, suggestionKey)}
                              >
                                <Send size={15} aria-hidden />
                                {sending ? "Enviando…" : "Enviar a escena"}
                              </Button>
                            </li>
                          );
                        })}
                      </ul>
                    </section>
                  )}

                  {response.suggestions.length > 0 && !isNarrative && (
                    <section className="master-result__section">
                      <h3>{meta.suggestionsTitle}</h3>
                      <ul>
                        {response.suggestions.map((suggestion) => (
                          <li key={suggestion}>{suggestion}</li>
                        ))}
                      </ul>
                    </section>
                  )}

                  {response.note && <p className="muted">{response.note}</p>}
                </div>
                );
              })()}
            </section>
          )}

          {tab === "settings" && (
            <section className="master-tab-panel">
              <CampaignSettingsForm campaignId={campaignId} campaign={campaign} />
            </section>
          )}
        </Panel>
      </div>

      {nextSceneOpen && (
        <NextSceneModal
          preparedScenes={preparedScenes}
          onPickPrepared={(sceneId) => {
            setNextSceneOpen(false);
            navigate(`/campaigns/${campaignId}/chat`);
            void api.activateScene(campaignId, sceneId).then(() => invalidateSceneQueries());
          }}
          onCreateNew={(displayName, objective) => {
            setNextSceneOpen(false);
            void api
              .createScene(campaignId, { displayName: displayName || undefined, sceneObjective: objective })
              .then(() => {
                invalidateSceneQueries();
                navigate(`/campaigns/${campaignId}/chat`);
              });
          }}
          onCancel={() => {
            setNextSceneOpen(false);
            navigate(campaignDefaultPath(campaignId, "MASTER", null));
          }}
        />
      )}

      <Toast message={toastMessage} onDismiss={() => setToastMessage(null)} />
    </RoleGate>
  );
}
