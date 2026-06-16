import type { CampaignMember } from "../../api/types";
import type { ChatMessage } from "../../api/types";
import {
  formatChatTimestamp,
  getInitials,
  MESSAGE_TYPE_META,
  normalizeMessageType,
} from "./messageTypes";
import { DiceRollCard } from "./DiceRollCard";

export type MemberLookup = Record<
  string,
  { display_name: string; role: CampaignMember["role"] }
>;

type ChatEntryProps = {
  message: ChatMessage;
  members: MemberLookup;
  currentUserId: string;
  memberCount: number;
};

export function ChatEntry({ message, members, currentUserId, memberCount }: ChatEntryProps) {
  const type = normalizeMessageType(message.type);

  if (type === "DICE_ROLL") {
    return (
      <DiceRollCard
        message={message}
        senderName={members[message.sender_id]?.display_name ?? message.sender_id.slice(0, 8)}
        timestamp={formatChatTimestamp(message.timestamp)}
        isOwn={message.sender_id === currentUserId}
      />
    );
  }

  const sender = members[message.sender_id];
  const isOwn = message.sender_id === currentUserId;
  const isMaster = sender?.role === "MASTER" || type === "MASTER";
  const meta = MESSAGE_TYPE_META[type] ?? MESSAGE_TYPE_META.ACTION;
  const readBy = message.read_by ?? [];
  const readersExcludingSender = readBy.filter((id) => id !== message.sender_id);
  const unreadCount = Math.max(memberCount - 1 - readersExcludingSender.length, 0);

  return (
    <article
      className={`chat-card ${isOwn ? "chat-card--own" : ""} ${isMaster ? "chat-card--master" : ""} chat-card--${meta.color}`}
    >
      <header className="chat-card__header">
        <div className="chat-card__identity">
          <span className="chat-card__avatar" aria-hidden>
            {getInitials(sender?.display_name ?? "?")}
          </span>
          <div>
            <strong>{sender?.display_name ?? "Desconocido"}</strong>
            <span className={`chat-card__type chat-card__type--${meta.color}`}>{meta.label}</span>
          </div>
        </div>
        <time className="chat-card__time">{formatChatTimestamp(message.timestamp)}</time>
      </header>
      <p className="chat-card__body">{message.text}</p>
      <footer className="chat-card__footer">
        <span className="chat-card__read" title={buildReadTooltip(readBy, members)}>
          👁 {readersExcludingSender.length}/{Math.max(memberCount - 1, 0)} leído
          {unreadCount > 0 && ` · ${unreadCount} pendiente`}
        </span>
      </footer>
    </article>
  );
}

function buildReadTooltip(readBy: string[], members: MemberLookup): string {
  if (readBy.length === 0) return "Nadie ha leído aún";
  return readBy.map((id) => members[id]?.display_name ?? id.slice(0, 8)).join(", ");
}
