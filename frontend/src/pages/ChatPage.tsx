import { FormEvent, useState } from "react";
import { api, Scene } from "../api/client";

const DEFAULT_CAMPAIGN = "00000000-0000-4000-8000-000000000001";

export function ChatPage() {
  const [scene, setScene] = useState<Scene | null>(null);
  const [message, setMessage] = useState("");
  const [dice, setDice] = useState("1d20");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function ensureScene() {
    if (scene) return scene;
    const created = await api.createScene(DEFAULT_CAMPAIGN, "Escena inicial de prueba");
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
      const updated = await api.postMessage(current.id, "player_1", message.trim());
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
      const updated = await api.rollDice(current.id, "player_1", dice.trim());
      setScene(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al tirar dados");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel chat-panel">
      <header className="panel-header">
        <div>
          <h2>Chat de escena</h2>
          <p>Turnos, narrativa y tiradas indexadas para memoria de campaña.</p>
        </div>
        {!scene && (
          <button className="button" onClick={handleStart} disabled={loading}>
            Crear escena demo
          </button>
        )}
      </header>

      {error && <p className="error">{error}</p>}

      <div className="chat-log">
        {scene?.scene_state.chat_buffer.length ? (
          scene.scene_state.chat_buffer.map((entry, index) => (
            <article key={`${entry.timestamp}-${index}`} className="chat-entry">
              <header>
                <strong>{entry.sender_id}</strong>
                <span>{entry.type}</span>
              </header>
              <p>{entry.text}</p>
            </article>
          ))
        ) : (
          <p className="muted">Aún no hay mensajes en la escena.</p>
        )}
      </div>

      <form className="chat-form" onSubmit={handleSend}>
        <input
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          placeholder="Describe la acción de tu personaje..."
          disabled={loading}
        />
        <button className="button" type="submit" disabled={loading || !message.trim()}>
          Enviar
        </button>
      </form>

      <div className="dice-row">
        <input value={dice} onChange={(event) => setDice(event.target.value)} disabled={loading} />
        <button className="button secondary" type="button" onClick={handleRoll} disabled={loading}>
          Tirar dados
        </button>
      </div>
    </section>
  );
}
