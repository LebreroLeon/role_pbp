import { FormEvent, useCallback, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";
import { ApiError } from "../api/http";
import { queryKeys } from "../api/queryKeys";
import type { MessageType, Scene } from "../api/types";
import { SECTION_ICONS } from "../components/icons";
import { Button, ButtonLink, ErrorBanner, Panel, PanelHeader, StatusBadge } from "../components/ui";
import { ChatComposer, ChatLog, DiceRoller, getChatBuffer, type MemberLookup } from "../features/scene";
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
import { useActiveSceneQuery } from "../hooks/queries/useSceneQueries";
import { useSceneWebSocket } from "../hooks/useSceneWebSocket";
import { useAuthStore } from "../stores/authStore";

export function ChatPage() {
  const { campaignId = "" } = useParams();
  const queryClient = useQueryClient();
  const currentUser = useAuthStore((state) => state.user);
  const currentUserId = currentUser?.id ?? "";

  const { data: campaign } = useCampaignQuery(campaignId);
  const { data: members = [] } = useCampaignMembersQuery(campaignId);
  const { data: entities = [] } = useEntitiesQuery(campaignId);
  const { data: activeScene, isLoading, isError, error, refetch } = useActiveSceneQuery(campaignId);

  const [scene, setScene] = useState<Scene | null>(null);
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState<MessageType>("ACTION");
  const [speakerId, setSpeakerId] = useState(DEFAULT_SPEAKER_OPTION_ID);
  const [dice, setDice] = useState("1d20");
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const currentScene = scene ?? activeScene ?? null;
  const isMaster = campaign?.role === "MASTER";

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

  const noActiveScene = !isLoading && isError && error instanceof ApiError && error.status === 404;

  async function handleStart() {
    setLoading(true);
    setErrorMessage(null);
    try {
      const created = await api.createScene(campaignId, "Escena inicial");
      setScene(created);
      queryClient.setQueryData(queryKeys.campaigns.activeScene(campaignId), created);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "No se pudo crear la escena");
    } finally {
      setLoading(false);
    }
  }

  async function handleSend(event: FormEvent) {
    event.preventDefault();
    if (!message.trim() || !currentScene) return;

    setLoading(true);
    setErrorMessage(null);
    const text = message.trim();
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

  async function handleRoll() {
    if (!currentScene) return;

    setLoading(true);
    setErrorMessage(null);
    const expression = dice.trim();

    const sent = sendDiceRoll(expression);
    if (sent) {
      setLoading(false);
      return;
    }

    try {
      const updated = await api.rollDice(currentScene.id, expression);
      handleSceneUpdate(updated);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Error al tirar dados");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="chat-page">
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
            members={memberLookup}
            isMaster={Boolean(isMaster)}
            onSceneUpdate={handleSceneUpdate}
          />
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
              {isMaster && (
                <ButtonLink variant="secondary" to={`/campaigns/${campaignId}/mesa`}>
                  Mesa del Máster
                </ButtonLink>
              )}
              <ButtonLink variant="secondary" to={`/campaigns/${campaignId}`}>
                Inicio
              </ButtonLink>
            </div>
          }
        />

        {errorMessage && <ErrorBanner message={errorMessage} />}

        {isLoading && <p className="muted">Cargando escena...</p>}

        {noActiveScene ? (
          <div className="actions">
            <Button onClick={handleStart} disabled={loading}>
              Iniciar escena
            </Button>
          </div>
        ) : currentScene ? (
          <>
            <ChatLog
              messages={getChatBuffer(currentScene.scene_state)}
              members={memberLookup}
              currentUserId={currentUserId}
              memberCount={members.length}
              emptyMessage="Aún no hay mensajes en la escena."
              onVisible={handleMarkRead}
            />

            <ChatComposer
              value={message}
              messageType={messageType}
              onChange={setMessage}
              onTypeChange={setMessageType}
              onSubmit={handleSend}
              disabled={loading || currentScene.status === "PAUSED"}
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
              disabled={loading || currentScene.status === "PAUSED"}
            />

            {currentScene.status === "PAUSED" && (
              <p className="muted chat-paused">La escena está congelada por el Máster.</p>
            )}
          </>
        ) : isError ? (
          <ErrorBanner message={error instanceof Error ? error.message : "No se pudo cargar la escena"} />
        ) : null}

        {!isLoading && !noActiveScene && !currentScene && (
          <Button onClick={() => refetch()} disabled={loading}>
            Reintentar carga
          </Button>
        )}
      </Panel>
    </div>
  );
}
