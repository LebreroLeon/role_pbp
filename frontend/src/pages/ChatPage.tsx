import { FormEvent, useCallback, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";
import { ApiError } from "../api/http";
import { queryKeys } from "../api/queryKeys";
import type { MessageType, Scene } from "../api/types";
import { Button, ErrorBanner, Panel, PanelHeader, StatusBadge } from "../components/ui";
import { ChatComposer, ChatLog, DiceRoller, type MemberLookup } from "../features/scene";
import { useCampaignMembersQuery, useCampaignQuery } from "../hooks/queries/useCampaignQueries";
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
  const { data: activeScene, isLoading, isError, error, refetch } = useActiveSceneQuery(campaignId);

  const [scene, setScene] = useState<Scene | null>(null);
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState<MessageType>("ACTION");
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
  });

  const handleMarkRead = useCallback(() => {
    if (!currentScene || !currentUserId) return;

    const buffer = currentScene.scene_state.chat_buffer;
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

    const sent = sendMessage(text, type);
    if (sent) {
      setLoading(false);
      return;
    }

    try {
      const updated = await api.postMessage(currentScene.id, text, type);
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
      <Panel className="chat-panel">
        <PanelHeader
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
                <Link className="button secondary" to={`/campaigns/${campaignId}/master`}>
                  Master Screen
                </Link>
              )}
              <Link className="button secondary" to={`/campaigns/${campaignId}`}>
                Hub
              </Link>
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
              messages={currentScene.scene_state.chat_buffer}
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
