import { FormEvent, useState } from "react";
import { api } from "../api/client";
import { Button, ErrorBanner, Panel, PanelHeader } from "../components/ui";
import { DEV_PLACEHOLDERS } from "../config/constants";
import { ChatForm, ChatLog, DiceRoller } from "../features/scene";
import type { Scene } from "../api/types";

export function ChatPage() {
  const [scene, setScene] = useState<Scene | null>(null);
  const [message, setMessage] = useState("");
  const [dice, setDice] = useState("1d20");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function ensureScene() {
    if (scene) return scene;
    const created = await api.createScene(DEV_PLACEHOLDERS.campaignId, "Escena inicial de prueba");
    setScene(created);
    return created;
  }

  async function handleStart() {
    setLoading(true);
    setError(null);
    try {
      await ensureScene();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo crear la escena");
    } finally {
      setLoading(false);
    }
  }

  async function handleSend(event: FormEvent) {
    event.preventDefault();
    if (!message.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const current = await ensureScene();
      const updated = await api.postMessage(current.id, DEV_PLACEHOLDERS.senderId, message.trim());
      setScene(updated);
      setMessage("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al enviar mensaje");
    } finally {
      setLoading(false);
    }
  }

  async function handleRoll() {
    setLoading(true);
    setError(null);
    try {
      const current = await ensureScene();
      const updated = await api.rollDice(current.id, DEV_PLACEHOLDERS.senderId, dice.trim());
      setScene(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al tirar dados");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Panel className="chat-panel">
      <PanelHeader
        title="Chat de escena"
        description="Turnos, narrativa y tiradas indexadas para memoria de campaña."
        actions={
          !scene ? (
            <Button onClick={handleStart} disabled={loading}>
              Crear escena demo
            </Button>
          ) : undefined
        }
      />

      {error && <ErrorBanner message={error} />}

      <div className="chat-log">
        <ChatLog messages={scene?.scene_state.chat_buffer ?? []} emptyMessage="Aún no hay mensajes en la escena." />
      </div>

      <ChatForm
        value={message}
        onChange={setMessage}
        onSubmit={handleSend}
        placeholder="Describe la acción de tu personaje..."
        disabled={loading}
      />

      <DiceRoller expression={dice} onExpressionChange={setDice} onRoll={handleRoll} disabled={loading} />
    </Panel>
  );
}
