import type { CampaignMember } from "../../api/types";
import type { ChatMessage } from "../../api/types";
import { CombatEntry } from "../combat/CombatEntry";
import { shouldRenderCombatEntry } from "../combat/combatMessage";
import { Eye } from "../../components/icons";
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

function resolveSpeakerPresentation(
  message: ChatMessage,
  members: MemberLookup,
  type: string,
): { displayName: string; isMasterVoice: boolean } {
  if (message.speaker_display_name) {
    const isMasterVoice =
      message.speaker_type === "NARRATOR" ||
      message.speaker_type === "MASTER" ||
      type === "MASTER";
    return { displayName: message.speaker_display_name, isMasterVoice };
  }

  const sender = members[message.sender_id];
  return {
    displayName: sender?.display_name ?? "Desconocido",
    isMasterVoice: sender?.role === "MASTER" || type === "MASTER",
  };
}

export function ChatEntry({ message, members, currentUserId, memberCount }: ChatEntryProps) {
  const type = normalizeMessageType(message.type);

  if (shouldRenderCombatEntry(message)) {
    return <CombatEntry message={message} members={members} currentUserId={currentUserId} />;
  }

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

  const isOwn = message.sender_id === currentUserId;
  const { displayName, isMasterVoice } = resolveSpeakerPresentation(message, members, type);
  const meta = MESSAGE_TYPE_META[type] ?? MESSAGE_TYPE_META.ACTION;
  const readBy = message.read_by ?? [];
  const readersExcludingSender = readBy.filter((id) => id !== message.sender_id);
  const unreadCount = Math.max(memberCount - 1 - readersExcludingSender.length, 0);

  return (
    <article
      className={`chat-card ${isOwn ? "chat-card--own" : ""} ${isMasterVoice ? "chat-card--master" : ""} chat-card--${meta.color}`}
    >
      <header className="chat-card__header">
        <div className="chat-card__identity">
          <span className="chat-card__avatar" aria-hidden>
            {getInitials(displayName)}
          </span>
          <div>
            <strong>{displayName}</strong>
            <span className={`chat-card__type chat-card__type--${meta.color}`}>{meta.label}</span>
          </div>
        </div>
        <time className="chat-card__time">{formatChatTimestamp(message.timestamp)}</time>
      </header>
      <p className="chat-card__body">{message.text}</p>
      <footer className="chat-card__footer">
        <span className="chat-card__read" title={buildReadTooltip(readBy, members)}>
          <Eye size={13} aria-hidden />
          {readersExcludingSender.length}/{Math.max(memberCount - 1, 0)} leído
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
