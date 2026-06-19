import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

import type { CampaignMember, OocMessage } from "../../api/types";
import { Button, ErrorBanner, Panel, PanelHeader, StatusBadge } from "../../components/ui";
import { SECTION_ICONS } from "../../components/icons";
import { useAuthStore } from "../../stores/authStore";

type RecipientMode = "all" | "whisper";

type OocChatPanelProps = {
  campaignId: string;
  members: CampaignMember[];
  messages: OocMessage[];
  connected: boolean;
  sending: boolean;
  errorMessage: string | null;
  onSendPublic: (content: string) => Promise<void>;
  onSendWhisper: (content: string, targetUserId: string) => Promise<void>;
};

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function mergeMessages(existing: OocMessage[], incoming: OocMessage[]): OocMessage[] {
  const byId = new Map(existing.map((message) => [message.id, message]));
  for (const message of incoming) {
    byId.set(message.id, message);
  }
  return [...byId.values()].sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
  );
}

export function mergeOocMessage(existing: OocMessage[], message: OocMessage): OocMessage[] {
  return mergeMessages(existing, [message]);
}

export function OocChatPanel({
  campaignId,
  members,
  messages,
  connected,
  sending,
  errorMessage,
  onSendPublic,
  onSendWhisper,
}: OocChatPanelProps) {
  const currentUserId = useAuthStore((state) => state.user?.id ?? "");
  const [draft, setDraft] = useState("");
  const [recipientMode, setRecipientMode] = useState<RecipientMode>("all");
  const [targetUserId, setTargetUserId] = useState("");
  const feedRef = useRef<HTMLDivElement>(null);

  const whisperTargets = useMemo(
    () => members.filter((member) => member.user_id !== currentUserId),
    [members, currentUserId],
  );

  useEffect(() => {
    if (recipientMode === "whisper" && !targetUserId && whisperTargets.length > 0) {
      setTargetUserId(whisperTargets[0]?.user_id ?? "");
    }
  }, [recipientMode, targetUserId, whisperTargets]);

  useEffect(() => {
    const feed = feedRef.current;
    if (!feed) return;
    feed.scrollTop = feed.scrollHeight;
  }, [messages.length]);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const content = draft.trim();
    if (!content || sending) return;

    if (recipientMode === "whisper") {
      if (!targetUserId) return;
      await onSendWhisper(content, targetUserId);
    } else {
      await onSendPublic(content);
    }
    setDraft("");
  };

  return (
    <Panel className="ooc-chat chat-panel">
      <PanelHeader
        icon={SECTION_ICONS.ooc}
        iconTone="violet"
        title="Fuera de personaje"
        description="Conversación libre entre jugadores y Máster, sin turnos ni escena activa."
        actions={
          <StatusBadge label="WS" value={connected ? "live" : "offline"} ok={connected} />
        }
      />

      {errorMessage ? <ErrorBanner message={errorMessage} /> : null}

      <div ref={feedRef} className="chat-log ooc-chat__messages">
        {messages.length === 0 ? (
          <p className="chat-log-empty">Todavía no hay mensajes OOC. Saluda al grupo.</p>
        ) : (
          <div className="chat-log-feed">
            {messages.map((message) => {
              const isOwn = message.author_user_id === currentUserId;
              const isWhisper = message.message_type === "OOC_WHISPER";
              return (
                <article
                  key={message.id}
                  className={[
                    "chat-card",
                    "ooc-chat__card",
                    isOwn ? "chat-card--own" : "",
                    isWhisper ? "ooc-chat__card--whisper" : "ooc-chat__card--public",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                >
                  <header className="chat-card__header">
                    <div className="chat-card__identity">
                      <span className="chat-card__avatar" aria-hidden>
                        {message.author_display_name.slice(0, 1).toUpperCase()}
                      </span>
                      <div className="chat-card__identity-text">
                        <strong>{message.author_display_name}</strong>
                        {isWhisper ? (
                          <span className="ooc-chat__whisper-label">
                            Susurro
                            {message.target_display_name ? ` → ${message.target_display_name}` : ""}
                          </span>
                        ) : (
                          <span className="chat-card__type chat-card__type--context">OOC</span>
                        )}
                      </div>
                    </div>
                    <time className="chat-card__time" dateTime={message.created_at}>
                      {formatTime(message.created_at)}
                    </time>
                  </header>
                  <p className="chat-card__body">{message.content}</p>
                </article>
              );
            })}
          </div>
        )}
      </div>

      <form className="chat-composer ooc-chat__composer" onSubmit={handleSubmit}>
        <div className="ooc-chat__recipient">
          <label className="ooc-chat__recipient-label" htmlFor={`ooc-recipient-${campaignId}`}>
            Destinatario
          </label>
          <select
            id={`ooc-recipient-${campaignId}`}
            className="chat-composer__speaker-select"
            value={recipientMode === "all" ? "all" : targetUserId}
            onChange={(event) => {
              const value = event.target.value;
              if (value === "all") {
                setRecipientMode("all");
                return;
              }
              setRecipientMode("whisper");
              setTargetUserId(value);
            }}
          >
            <option value="all">Todos (público OOC)</option>
            {whisperTargets.map((member) => (
              <option key={member.user_id} value={member.user_id}>
                Susurro a {member.display_name}
              </option>
            ))}
          </select>
        </div>

        <textarea
          className="chat-composer__input"
          rows={3}
          placeholder={
            recipientMode === "whisper"
              ? "Mensaje privado fuera de personaje..."
              : "Mensaje para toda la mesa..."
          }
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          disabled={sending}
        />

        <div className="ooc-chat__actions">
          <Button type="submit" disabled={sending || !draft.trim()}>
            {sending ? "Enviando..." : recipientMode === "whisper" ? "Enviar susurro" : "Enviar OOC"}
          </Button>
        </div>
      </form>
    </Panel>
  );
}
