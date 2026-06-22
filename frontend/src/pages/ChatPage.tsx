import { FormEvent, useCallback, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";
import { queryKeys } from "../api/queryKeys";
import type { LoreAssistResponse, MasterBriefingResponse, MessageType, Scene, ScenePickerItem } from "../api/types";
import { SECTION_ICONS } from "../components/icons";
import {
  Button,
  ConfirmDialog,
  ErrorBanner,
  Panel,
  PanelHeader,
  StatusBadge,
  Toast,
} from "../components/ui";
import { ChatComposer, ChatLog, DiceRoller, getChatBuffer, MasterBriefingModal, MasterCheatSheet, NextSceneModal, type MemberLookup } from "../features/scene";
import { GameSystemChatMiniSheet, type AdvantageMode } from "../features/systems";
import {
  canUserPostInPbp,
  isPbpEnabled,
  resolveCurrentTurnLabel,
} from "../features/scene/sceneState";
import { formatSceneLabel, campaignDefaultPath } from "../features/campaign";
import { buildMentionOptions } from "../features/scene/mentionOptions";
import {
  buildSpeakerOptions,
  DEFAULT_SPEAKER_OPTION_ID,
  speakerOptionToPayload,
  type SpeakerPayload,
} from "../features/scene/speakerOptions";
import { InitiativeOrderPanel, SceneRosterPanel } from "../features/combat";
import { useCampaignMembersQuery, useCampaignQuery } from "../hooks/queries/useCampaignQueries";
import { useEntitiesQuery } from "../hooks/queries/useEntityQueries";
import { useOpenSceneQuery } from "../hooks/queries/useSceneQueries";
import { useSceneWebSocket } from "../hooks/useSceneWebSocket";
import { useAuthStore } from "../stores/authStore";

export function ChatPage() {
  const { campaignId = "" } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const currentUser = useAuthStore((state) => state.user);
  const currentUserId = currentUser?.id ?? "";

  const { data: campaign } = useCampaignQuery(campaignId);
  const { data: members = [] } = useCampaignMembersQuery(campaignId);
  const { data: entities = [] } = useEntitiesQuery(campaignId);
  const { data: openScene, isLoading: sceneLoading, refetch } = useOpenSceneQuery(campaignId);

  const [scene, setScene] = useState<Scene | null>(null);
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState<MessageType>("ACTION");
  const [speakerId, setSpeakerId] = useState(DEFAULT_SPEAKER_OPTION_ID);
  const [dice, setDice] = useState("1d20");
  const [diceAdvantageMode, setDiceAdvantageMode] = useState<AdvantageMode>("normal");
  const [diceMasterOnly, setDiceMasterOnly] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [newSceneName, setNewSceneName] = useState("");
  const [newSceneObjective, setNewSceneObjective] = useState("");
  const [newSceneLocationId, setNewSceneLocationId] = useState("");
  const [closeDialogOpen, setCloseDialogOpen] = useState(false);
  const [closing, setClosing] = useState(false);
  const [preparedScenes, setPreparedScenes] = useState<ScenePickerItem[]>([]);
  const [nextSceneOpen, setNextSceneOpen] = useState(false);
  const [nextSceneLoading, setNextSceneLoading] = useState(false);
  const [activateBriefing, setActivateBriefing] = useState<MasterBriefingResponse | null>(null);
  const [sendOpeningOnActivate, setSendOpeningOnActivate] = useState(true);
  const [freezeDialogOpen, setFreezeDialogOpen] = useState(false);
  const [freezing, setFreezing] = useState(false);
  const [deleteMessageId, setDeleteMessageId] = useState<string | null>(null);
  const [deletingMessage, setDeletingMessage] = useState(false);
  const [togglingLikeId, setTogglingLikeId] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [loreAssistHistory, setLoreAssistHistory] = useState<LoreAssistResponse[]>([]);

  const currentScene = scene ?? openScene ?? null;
  const isMaster = campaign?.role === "MASTER";
  const noOpenScene = !sceneLoading && !openScene;

  const memberLookup = useMemo<MemberLookup>(() => {
    const lookup: MemberLookup = {};
    for (const member of members) {
      lookup[member.user_id] = { display_name: member.display_name, role: member.role };
    }
    return lookup;
  }, [members]);

  const mentionOptions = useMemo(
    () => buildMentionOptions(currentScene?.scene_state, entities),
    [currentScene?.scene_state, entities],
  );

  const speakerOptions = useMemo(() => buildSpeakerOptions(entities), [entities]);

  const selectedSpeakerPayload = useMemo((): SpeakerPayload | undefined => {
    if (!isMaster) return undefined;
    const option = speakerOptions.find((item) => item.id === speakerId);
    return option ? speakerOptionToPayload(option) : undefined;
  }, [isMaster, speakerId, speakerOptions]);

  const locations = useMemo(
    () => entities.filter((entity) => entity.entity_type === "LOCATION"),
    [entities],
  );

  const handleSceneUpdate = useCallback(
    (updated: Scene) => {
      setScene(updated);
      queryClient.setQueryData(queryKeys.campaigns.activeScene(campaignId), updated);
    },
    [campaignId, queryClient],
  );

  const { connected, sendMessage, sendDiceRoll, markRead } = useSceneWebSocket({
    sceneId: currentScene?.id ?? null,
    onSceneUpdate: handleSceneUpdate,
    onError: setErrorMessage,
  });

  const canPostInPbp = useMemo(() => {
    if (!currentScene || isMaster) return true;
    return canUserPostInPbp(currentScene.scene_state, currentUserId, Boolean(isMaster), entities);
  }, [currentScene, currentUserId, isMaster, entities]);

  const pbpTurnLabel = useMemo(() => {
    if (!currentScene) return null;
    return resolveCurrentTurnLabel(currentScene.scene_state, memberLookup, entities, Boolean(isMaster));
  }, [currentScene, memberLookup, entities, isMaster]);

  const pbpEnabled = currentScene ? isPbpEnabled(currentScene.scene_state) : false;
  const composerDisabled =
    loading || currentScene?.status === "PAUSED" || (pbpEnabled && !canPostInPbp && !isMaster);

  const handleMarkRead = useCallback(() => {
    if (!currentScene || !currentUserId) return;

    const buffer = getChatBuffer(currentScene.scene_state);
    const allRead = buffer.every(
      (message) => message.sender_id === currentUserId || (message.read_by ?? []).includes(currentUserId),
    );
    if (allRead) return;

    const sent = markRead();
    if (!sent) {
      api.markSceneRead(currentScene.id).then(handleSceneUpdate).catch(() => undefined);
    }
  }, [currentScene, currentUserId, markRead, handleSceneUpdate]);

  async function handleStart() {
    setLoading(true);
    setErrorMessage(null);
    try {
      const created = await api.createScene(campaignId, {
        sceneObjective: newSceneObjective.trim() || undefined,
        displayName: newSceneName.trim() || undefined,
        locationId: newSceneLocationId || undefined,
      });
      setScene(created);
      queryClient.setQueryData(queryKeys.campaigns.activeScene(campaignId), created);
      queryClient.invalidateQueries({ queryKey: queryKeys.campaigns.scenes(campaignId) });
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "No se pudo crear la escena");
    } finally {
      setLoading(false);
    }
  }

  async function handleActivatePrepared(sceneId: string, sendOpening: boolean) {
    setNextSceneLoading(true);
    setErrorMessage(null);
    try {
      const activated = await api.activateScene(campaignId, sceneId, { sendOpeningToChat: sendOpening });
      setScene(activated);
      queryClient.setQueryData(queryKeys.campaigns.activeScene(campaignId), activated);
      await queryClient.invalidateQueries({ queryKey: queryKeys.campaigns.scenes(campaignId) });
      await queryClient.invalidateQueries({ queryKey: queryKeys.entities.all(campaignId) });
      setNextSceneOpen(false);
      setActivateBriefing(null);
      setPreparedScenes([]);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "No se pudo activar la escena");
    } finally {
      setNextSceneLoading(false);
    }
  }

  async function handlePickPreparedScene(sceneId: string) {
    setNextSceneLoading(true);
    setErrorMessage(null);
    try {
      const briefing = await api.getMasterBriefing(campaignId, sceneId);
      setActivateBriefing(briefing);
      setSendOpeningOnActivate(Boolean(briefing.opening_narration?.trim()));
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "No se pudo cargar el briefing");
    } finally {
      setNextSceneLoading(false);
    }
  }

  async function handleCreateNextScene(displayName: string, objective: string) {
    setNextSceneLoading(true);
    setErrorMessage(null);
    try {
      const created = await api.createScene(campaignId, {
        displayName: displayName || undefined,
        sceneObjective: objective,
      });
      setScene(created);
      queryClient.setQueryData(queryKeys.campaigns.activeScene(campaignId), created);
      await queryClient.invalidateQueries({ queryKey: queryKeys.campaigns.scenes(campaignId) });
      setNextSceneOpen(false);
      setPreparedScenes([]);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "No se pudo crear la escena");
    } finally {
      setNextSceneLoading(false);
    }
  }

  async function handleSend(event: FormEvent) {
    event.preventDefault();
    if (!message.trim() || !currentScene) return;

    const text = message.trim();
    const loreMatch = text.match(/^@asistente\s+(.+)/i);
    if (loreMatch && !isMaster) {
      setLoading(true);
      setErrorMessage(null);
      setMessage("");
      try {
        const response = await api.loreAssist(currentScene.id, loreMatch[1].trim());
        setLoreAssistHistory((current) => [response, ...current].slice(0, 3));
        setToastMessage(
          `${response.answer}${response.note ? ` (${response.note})` : ""} — Quedan ${response.remaining_tokens} consultas.`,
        );
        await refetch();
      } catch (err) {
        setErrorMessage(err instanceof Error ? err.message : "No se pudo consultar al asistente");
      } finally {
        setLoading(false);
      }
      return;
    }

    setLoading(true);
    setErrorMessage(null);
    const type = messageType;
    setMessage("");

    const sent = sendMessage(text, type, selectedSpeakerPayload);
    if (sent) {
      setLoading(false);
      return;
    }

    try {
      const updated = await api.postMessage(currentScene.id, text, type, selectedSpeakerPayload);
      handleSceneUpdate(updated);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Error al enviar mensaje");
    } finally {
      setLoading(false);
    }
  }

  async function handleRoll(options?: { advantage?: boolean; disadvantage?: boolean; masterOnly?: boolean }) {
    if (!currentScene) return;

    setLoading(true);
    setErrorMessage(null);
    const expression = dice.trim();

    const sent = sendDiceRoll(expression, options);
    if (sent) {
      setLoading(false);
      return;
    }

    try {
      const updated = await api.rollDice(currentScene.id, expression, options);
      handleSceneUpdate(updated);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Error al tirar dados");
    } finally {
      setLoading(false);
    }
  }

  function requestDeleteMessage(messageId: string) {
    setDeleteMessageId(messageId);
  }

  async function handleToggleLike(messageId: string) {
    if (!currentScene) return;

    setTogglingLikeId(messageId);
    setErrorMessage(null);
    try {
      const updated = await api.toggleSceneMessageLike(currentScene.id, messageId);
      handleSceneUpdate(updated);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "No se pudo actualizar el me gusta");
    } finally {
      setTogglingLikeId(null);
    }
  }

  async function confirmDeleteMessage() {
    if (!currentScene || !deleteMessageId || !isMaster) return;

    setDeletingMessage(true);
    setErrorMessage(null);
    try {
      const updated = await api.deleteSceneMessage(currentScene.id, deleteMessageId);
      handleSceneUpdate(updated);
      setDeleteMessageId(null);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "No se pudo borrar el mensaje");
    } finally {
      setDeletingMessage(false);
    }
  }

  async function handleCloseScene() {
    if (!currentScene || !isMaster) return;

    setClosing(true);
    setErrorMessage(null);
    try {
      const result = await api.closeScene(currentScene.id);
      queryClient.removeQueries({ queryKey: queryKeys.campaigns.activeScene(campaignId) });
      await queryClient.invalidateQueries({ queryKey: queryKeys.campaigns.scenes(campaignId) });
      setScene(null);
      setCloseDialogOpen(false);
      setPreparedScenes(result.prepared_scenes);
      setNextSceneOpen(true);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "No se pudo cerrar la escena");
    } finally {
      setClosing(false);
    }
  }

  async function handleUpdateSceneStatus(nextStatus: "ACTIVE" | "PAUSED") {
    if (!currentScene || !isMaster) return;

    setFreezing(true);
    setErrorMessage(null);
    try {
      const updated = await api.updateSceneStatus(currentScene.id, nextStatus);
      handleSceneUpdate(updated);
      await queryClient.invalidateQueries({ queryKey: queryKeys.campaigns.scenes(campaignId) });
      setFreezeDialogOpen(false);
      setToastMessage(nextStatus === "PAUSED" ? "Escena congelada." : "Escena reanudada.");
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "No se pudo cambiar el estado de la escena");
    } finally {
      setFreezing(false);
    }
  }

  function handleFreezeClick() {
    if (!currentScene || currentScene.status === "CLOSED") return;
    if (currentScene.status === "PAUSED") {
      void handleUpdateSceneStatus("ACTIVE");
      return;
    }
    setFreezeDialogOpen(true);
  }

  return (
    <div className="chat-page">
      <Toast message={toastMessage} onDismiss={() => setToastMessage(null)} />
      {currentScene && (
        <aside className="chat-page__sidebar">
          <SceneRosterPanel
            sceneId={currentScene.id}
            campaignId={campaignId}
            gameSystem={campaign?.game_system}
            sceneState={currentScene.scene_state}
            entities={entities}
            currentUserId={currentUserId}
            isMaster={Boolean(isMaster)}
            disabled={loading || currentScene.status === "PAUSED"}
            onSceneUpdate={handleSceneUpdate}
          />
          <InitiativeOrderPanel
            sceneId={currentScene.id}
            campaignId={campaignId}
            sceneState={currentScene.scene_state}
            entities={entities}
            members={memberLookup}
            isMaster={Boolean(isMaster)}
            onSceneUpdate={handleSceneUpdate}
          />
          {isMaster && <MasterCheatSheet campaignId={campaignId} scene={currentScene} />}
          {!isMaster && loreAssistHistory.length > 0 && (
            <aside className="lore-assist-panel" aria-label="Respuestas del asistente">
              <h3 className="lore-assist-panel__title">@asistente</h3>
              <p className="muted lore-assist-panel__hint">Últimas consultas en esta sesión.</p>
              <ul className="lore-assist-panel__list">
                {loreAssistHistory.map((entry) => (
                  <li key={entry.generated_at} className="lore-assist-panel__item">
                    <p className="lore-assist-panel__query">{entry.query}</p>
                    <p className="lore-assist-panel__answer">{entry.answer}</p>
                    {entry.note && <p className="muted lore-assist-panel__note">{entry.note}</p>}
                    <p className="muted lore-assist-panel__meta">
                      Quedan {entry.remaining_tokens} consultas
                    </p>
                  </li>
                ))}
              </ul>
            </aside>
          )}
        </aside>
      )}

      <Panel className="chat-panel">
        <PanelHeader
          icon={SECTION_ICONS.chat}
          iconTone="rose"
          title="Chat de escena"
          description="Diálogo, acción y contexto en tiempo real."
          actions={
            <div className="status-row">
              {currentScene && (
                <StatusBadge
                  label="WS"
                  value={connected ? "live" : "offline"}
                  ok={connected}
                />
              )}
              {isMaster && currentScene && currentScene.status !== "CLOSED" && (
                <>
                  <Button variant="secondary" onClick={handleFreezeClick} disabled={freezing}>
                    {currentScene.status === "PAUSED" ? "Reanudar escena" : "Congelar escena"}
                  </Button>
                  <Button variant="secondary" onClick={() => setCloseDialogOpen(true)} disabled={closing}>
                    Cerrar escena
                  </Button>
                </>
              )}
            </div>
          }
        />

        {errorMessage && <ErrorBanner message={errorMessage} />}

        {sceneLoading && <p className="muted">Cargando escena...</p>}

        {noOpenScene && !isMaster ? (
          <div className="chat-start">
            <p className="muted">Esperando al Máster. Cuando inicie la siguiente escena podrás entrar al chat.</p>
          </div>
        ) : noOpenScene && isMaster ? (
          <div className="chat-start">
            <label className="field-label" htmlFor="new-scene-name">
              Nombre de la escena
            </label>
            <input
              id="new-scene-name"
              type="text"
              value={newSceneName}
              onChange={(event) => setNewSceneName(event.target.value)}
              placeholder='Ej. "La taberna del Grifo"'
              maxLength={200}
              disabled={loading}
            />
            <label className="field-label" htmlFor="new-scene-objective">
              Objetivo
            </label>
            <textarea
              id="new-scene-objective"
              value={newSceneObjective}
              onChange={(event) => setNewSceneObjective(event.target.value)}
              rows={2}
              placeholder="Qué debe ocurrir en esta escena"
              disabled={loading}
            />
            {locations.length > 0 && (
              <>
                <label className="field-label" htmlFor="new-scene-location">
                  Ubicación
                </label>
                <select
                  id="new-scene-location"
                  value={newSceneLocationId}
                  onChange={(event) => setNewSceneLocationId(event.target.value)}
                  disabled={loading}
                >
                  <option value="">Sin ubicación</option>
                  {locations.map((location) => {
                    const identity = location.document.identity as { name?: string } | undefined;
                    return (
                      <option key={location.id} value={location.id}>
                        {identity?.name ?? location.id.slice(0, 8)}
                      </option>
                    );
                  })}
                </select>
              </>
            )}
            <div className="actions">
              <Button onClick={handleStart} disabled={loading || !newSceneObjective.trim()}>
                Iniciar escena
              </Button>
            </div>
          </div>
        ) : currentScene ? (
          <>
            <p className="muted chat-scene-label">{formatSceneLabel(currentScene)}</p>
            <ChatLog
              messages={getChatBuffer(currentScene.scene_state)}
              members={memberLookup}
              currentUserId={currentUserId}
              memberCount={members.length}
              emptyMessage="Aún no hay mensajes en la escena."
              onVisible={handleMarkRead}
              isMaster={Boolean(isMaster)}
              onDeleteMessage={isMaster ? requestDeleteMessage : undefined}
              onToggleLike={handleToggleLike}
              togglingLikeId={togglingLikeId}
              entities={entities}
              sceneState={currentScene.scene_state}
            />

            {pbpEnabled && pbpTurnLabel && (
              <p className="chat-pbp-banner" role="status">
                Turno de <strong>{pbpTurnLabel}</strong>
                {!canPostInPbp && !isMaster && " — espera tu turno para escribir."}
              </p>
            )}

            <ChatComposer
              value={message}
              messageType={messageType}
              onChange={setMessage}
              onTypeChange={setMessageType}
              onSubmit={handleSend}
              disabled={composerDisabled}
              isMaster={Boolean(isMaster)}
              mentionOptions={mentionOptions}
              speakerOptions={speakerOptions}
              speakerId={speakerId}
              onSpeakerChange={setSpeakerId}
            />

            <DiceRoller
              expression={dice}
              onExpressionChange={setDice}
              onRoll={handleRoll}
              disabled={composerDisabled}
              gameSystem={campaign?.game_system ?? undefined}
              advantageMode={diceAdvantageMode}
              onAdvantageModeChange={setDiceAdvantageMode}
              isMaster={Boolean(isMaster)}
              masterOnly={diceMasterOnly}
              onMasterOnlyChange={setDiceMasterOnly}
            />

            <GameSystemChatMiniSheet
              campaignId={campaignId}
              gameSystem={campaign?.game_system ?? undefined}
              disabled={composerDisabled}
              onSceneRefresh={() => refetch()}
            />

            {currentScene.status === "PAUSED" && (
              <p className="muted chat-paused">La escena está congelada por el Máster.</p>
            )}
          </>
        ) : null}

        {!sceneLoading && !noOpenScene && !currentScene && (
          <Button onClick={() => refetch()} disabled={loading}>
            Reintentar carga
          </Button>
        )}
      </Panel>

      {deleteMessageId && (
        <ConfirmDialog
          title="Eliminar mensaje"
          description="¿Seguro que quieres eliminar esto del registro?"
          confirmLabel="Eliminar"
          onConfirm={confirmDeleteMessage}
          onCancel={() => setDeleteMessageId(null)}
          confirming={deletingMessage}
        />
      )}

      {freezeDialogOpen && (
        <ConfirmDialog
          title="Congelar escena"
          description={
            <p className="muted">
              Los jugadores no podrán enviar mensajes ni tirar dados hasta que reanudes la escena.
            </p>
          }
          confirmLabel="Congelar"
          onConfirm={() => handleUpdateSceneStatus("PAUSED")}
          onCancel={() => setFreezeDialogOpen(false)}
          confirming={freezing}
        />
      )}

      {closeDialogOpen && (
        <ConfirmDialog
          title="Cerrar escena"
          description={
            <>
              <p>
                Se enviará todo el chat de la escena a la IA para generar un resumen narrativo en español (WorldLog).
              </p>
              <p className="muted">
                El resumen quedará guardado en el historial de escenas y en la memoria de campaña. Esta acción no se
                puede deshacer.
              </p>
            </>
          }
          confirmLabel="Cerrar y generar resumen"
          onConfirm={handleCloseScene}
          onCancel={() => setCloseDialogOpen(false)}
          confirming={closing}
        />
      )}

      {nextSceneOpen && (
        <NextSceneModal
          preparedScenes={preparedScenes}
          loading={nextSceneLoading}
          onPickPrepared={handlePickPreparedScene}
          onCreateNew={handleCreateNextScene}
          onCancel={() => {
            setNextSceneOpen(false);
            navigate(campaignDefaultPath(campaignId, "MASTER", null));
          }}
        />
      )}

      {activateBriefing && (
        <MasterBriefingModal
          briefing={activateBriefing}
          activating={nextSceneLoading}
          sendOpening={sendOpeningOnActivate}
          onSendOpeningChange={setSendOpeningOnActivate}
          onActivate={() => handleActivatePrepared(activateBriefing.scene_id, sendOpeningOnActivate)}
          onCancel={() => setActivateBriefing(null)}
        />
      )}
    </div>
  );
}
