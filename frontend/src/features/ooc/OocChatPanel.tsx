import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

import type { CampaignMember, OocMessage } from "../../api/types";
import { Button, ConfirmDialog, ErrorBanner, Panel, PanelHeader, StatusBadge } from "../../components/ui";
import { SECTION_ICONS } from "../../components/icons";
import { useAuthStore } from "../../stores/authStore";
import { ChatMessageDeleteButton } from "../scene/ChatMessageDeleteButton";
import {
  buildOocChannelTabs,
  filterMessagesByChannel,
  findMasterMembers,
  type OocChannelId,
  resolveWhisperTarget,
} from "./oocChannels";

type OocChatPanelProps = {
  members: CampaignMember[];
  viewerRole: "MASTER" | "PLAYER";
  messages: OocMessage[];
  activeChannel: OocChannelId;
  onChannelChange: (channel: OocChannelId) => void;
  connected: boolean;
  sending: boolean;
  errorMessage: string | null;
  onSendPublic: (content: string) => Promise<void>;
  onSendWhisper: (content: string, targetUserId: string) => Promise<void>;
  onDeleteMessage?: (messageId: string) => void;
  deleteMessageId?: string | null;
  onConfirmDelete?: () => void;
  onCancelDelete?: () => void;
  deletingMessage?: boolean;
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

export function removeOocMessage(existing: OocMessage[], messageId: string): OocMessage[] {
  return existing.filter((message) => message.id !== messageId);
}

export function OocChatPanel({
  members,
  viewerRole,
  messages,
  activeChannel,
  onChannelChange,
  connected,
  sending,
  errorMessage,
  onSendPublic,
  onSendWhisper,
  onDeleteMessage,
  deleteMessageId = null,
  onConfirmDelete,
  onCancelDelete,
  deletingMessage = false,
}: OocChatPanelProps) {
  const currentUserId = useAuthStore((state) => state.user?.id ?? "");
  const [draft, setDraft] = useState("");
  const feedRef = useRef<HTMLDivElement>(null);

  const masterMembers = useMemo(() => findMasterMembers(members), [members]);
  const masterUserIds = useMemo(() => masterMembers.map((member) => member.user_id), [masterMembers]);
  const channelTabs = useMemo(
    () => buildOocChannelTabs(members, viewerRole),
    [members, viewerRole],
  );

  const channelMessages = useMemo(
    () => filterMessagesByChannel(messages, activeChannel, currentUserId, masterUserIds),
    [messages, activeChannel, currentUserId, masterUserIds],
  );

  const isPrivateChannel = activeChannel !== "all";
  const isMaster = viewerRole === "MASTER";

  useEffect(() => {
    const feed = feedRef.current;
    if (!feed) return;
    feed.scrollTop = feed.scrollHeight;
  }, [channelMessages.length, activeChannel]);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const content = draft.trim();
    if (!content || sending) return;

    if (isPrivateChannel) {
      const targetUserId = resolveWhisperTarget(activeChannel, masterUserIds);
      if (!targetUserId) return;
      await onSendWhisper(content, targetUserId);
    } else {
      await onSendPublic(content);
    }
    setDraft("");
  };

  const activeTab = channelTabs.find((tab) => tab.id === activeChannel) ?? channelTabs[0];

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

      <nav className="ooc-chat__tabs master-tabs" role="tablist" aria-label="Canales OOC">
        {channelTabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={activeChannel === tab.id}
            className={`master-tabs__btn ooc-chat__tab ${activeChannel === tab.id ? "is-active" : ""}`}
            onClick={() => onChannelChange(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {errorMessage ? <ErrorBanner message={errorMessage} /> : null}

      <div ref={feedRef} className="chat-log ooc-chat__messages">
        {channelMessages.length === 0 ? (
          <p className="chat-log-empty">
            {activeChannel === "all"
              ? "Todavía no hay mensajes OOC. Saluda al grupo."
              : `Sin mensajes en ${activeTab?.label ?? "este canal"}.`}
          </p>
        ) : (
          <div className="chat-log-feed">
            {channelMessages.map((message) => {
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
                            Privado
                            {message.target_display_name ? ` → ${message.target_display_name}` : ""}
                          </span>
                        ) : (
                          <span className="chat-card__type chat-card__type--context">OOC</span>
                        )}
                      </div>
                    </div>
                    <div className="chat-card__meta">
                      {isMaster && onDeleteMessage && (
                        <ChatMessageDeleteButton onClick={() => onDeleteMessage(message.id)} />
                      )}
                      <time className="chat-card__time" dateTime={message.created_at}>
                        {formatTime(message.created_at)}
                      </time>
                    </div>
                  </header>
                  <p className="chat-card__body">{message.content}</p>
                </article>
              );
            })}
          </div>
        )}
      </div>

      <form className="chat-composer ooc-chat__composer" onSubmit={handleSubmit}>
        <textarea
          className="chat-composer__input"
          rows={3}
          placeholder={
            isPrivateChannel
              ? `Mensaje privado con ${activeTab?.label ?? "Máster"}...`
              : "Mensaje para toda la mesa..."
          }
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          disabled={sending}
          aria-label={`Mensaje OOC en ${activeTab?.label ?? "canal"}`}
        />

        <div className="ooc-chat__actions">
          <Button type="submit" disabled={sending || !draft.trim()}>
            {sending ? "Enviando..." : isPrivateChannel ? "Enviar privado" : "Enviar OOC"}
          </Button>
        </div>
      </form>

      {deleteMessageId && onConfirmDelete && onCancelDelete && (
        <ConfirmDialog
          title="Eliminar mensaje OOC"
          description="¿Seguro que quieres eliminar este mensaje del chat fuera de personaje?"
          confirmLabel="Eliminar"
          onConfirm={onConfirmDelete}
          onCancel={onCancelDelete}
          confirming={deletingMessage}
        />
      )}
    </Panel>
  );
}
