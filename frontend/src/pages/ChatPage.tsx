import { FormEvent, useCallback, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";
import { ApiError } from "../api/http";
import { queryKeys } from "../api/queryKeys";
import type { Scene } from "../api/types";
import { Button, ErrorBanner, Panel, PanelHeader, StatusBadge } from "../components/ui";
import { ChatForm, ChatLog, DiceRoller } from "../features/scene";
import { useActiveSceneQuery } from "../hooks/queries/useSceneQueries";
import { useSceneWebSocket } from "../hooks/useSceneWebSocket";

export function ChatPage() {
  const { campaignId = "" } = useParams();
  const queryClient = useQueryClient();
  const { data: activeScene, isLoading, isError, error, refetch } = useActiveSceneQuery(campaignId);

  const [scene, setScene] = useState<Scene | null>(null);
  const [message, setMessage] = useState("");
  const [dice, setDice] = useState("1d20");
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const currentScene = scene ?? activeScene ?? null;

  const handleSceneUpdate = useCallback(
    (updated: Scene) => {
      setScene(updated);
      queryClient.setQueryData(queryKeys.campaigns.activeScene(campaignId), updated);
    },
    [campaignId, queryClient],
  );

  const { connected, sendMessage, sendDiceRoll } = useSceneWebSocket({
    sceneId: currentScene?.id ?? null,
    onSceneUpdate: handleSceneUpdate,
  });

  const noActiveScene = !isLoading && (isError && error instanceof ApiError && error.status === 404);

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
    setMessage("");

    const sent = sendMessage(text);
    if (sent) {
      setLoading(false);
      return;
    }

    try {
      const updated = await api.postMessage(currentScene.id, text);
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
    <Panel className="chat-panel">
      <PanelHeader
        title="Chat de escena"
        description="Turnos, narrativa y tiradas en tiempo real."
        actions={
          <div className="status-row">
            {currentScene && <StatusBadge label="WS" value={connected ? "live" : "offline"} ok={connected} />}
            <Link className="button secondary" to={`/campaigns/${campaignId}`}>
              Volver al hub
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
          <div className="chat-log">
            <ChatLog
              messages={currentScene.scene_state.chat_buffer}
              emptyMessage="Aún no hay mensajes en la escena."
            />
          </div>

          <ChatForm
            value={message}
            onChange={setMessage}
            onSubmit={handleSend}
            placeholder="Describe la acción de tu personaje..."
            disabled={loading}
          />

          <DiceRoller expression={dice} onExpressionChange={setDice} onRoll={handleRoll} disabled={loading} />
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
  );
}
