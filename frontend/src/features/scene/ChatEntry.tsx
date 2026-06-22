import type { CampaignEntity, CampaignMember, ChatMessage } from "../../api/types";
import { CombatEntry } from "../combat/CombatEntry";
import { resolveCombatEntityName, shouldRenderCombatEntry } from "../combat/combatMessage";
import type { SceneStateInput } from "./sceneState";
import { Eye } from "../../components/icons";
import { Tooltip } from "../../components/ui";
import { ChatIllustrationPreviewIcon } from "./ChatIllustrationPreviewIcon";
import { ChatMessageDeleteButton } from "./ChatMessageDeleteButton";
import { resolveMessageAvatarUrl } from "../entities/entityAvatar";
import { ChatAvatar } from "./ChatAvatar";
import {
  formatChatTimestamp,
  MESSAGE_TYPE_META,
  normalizeMessageType,
} from "./messageTypes";
import { DiceRollCard } from "./DiceRollCard";
import { MasterOnlyMessageBadge } from "./MasterOnlyMessageBadge";
import { MessageLikeBadge } from "./MessageLikeBadge";
import { isMasterOnlyMessage } from "./messageVisibility";

export type MemberLookup = Record<
  string,
  { display_name: string; role: CampaignMember["role"] }
>;

type ChatEntryProps = {
  message: ChatMessage;
  members: MemberLookup;
  currentUserId: string;
  memberCount: number;
  isMaster?: boolean;
  onDelete?: (messageId: string) => void;
  onToggleLike?: (messageId: string) => void;
  togglingLikeId?: string | null;
  entities?: CampaignEntity[];
  sceneState?: SceneStateInput | null;
};

const FALLBACK_NARRATOR_NAME = "Máster / Narrador";
const FALLBACK_CHARACTER_NAME = "Personaje";
const MASTER_DICE_ROLL_NAME = "Máster";

function resolveCharacterName(
  message: ChatMessage,
  members: MemberLookup,
  type: string,
): string {
  if (message.speaker_display_name) {
    return message.speaker_display_name;
  }
  const sender = members[message.sender_id];
  if (sender?.role === "MASTER" || type === "MASTER") {
    return FALLBACK_NARRATOR_NAME;
  }
  return FALLBACK_CHARACTER_NAME;
}

function resolvePlayerName(message: ChatMessage, members: MemberLookup): string {
  return members[message.sender_id]?.display_name ?? "Desconocido";
}

function isMasterVoice(message: ChatMessage, members: MemberLookup, type: string): boolean {
  if (message.speaker_display_name) {
    return (
      message.speaker_type === "NARRATOR" ||
      message.speaker_type === "MASTER" ||
      type === "MASTER"
    );
  }
  const sender = members[message.sender_id];
  return sender?.role === "MASTER" || type === "MASTER";
}

export function ChatEntry({
  message,
  members,
  currentUserId,
  memberCount,
  isMaster = false,
  onDelete,
  onToggleLike,
  togglingLikeId = null,
  entities,
  sceneState,
}: ChatEntryProps) {
  const type = normalizeMessageType(message.type);

  if (shouldRenderCombatEntry(message)) {
    return (
      <CombatEntry
        message={message}
        members={members}
        currentUserId={currentUserId}
        isMaster={isMaster}
        onDelete={onDelete}
        onToggleLike={onToggleLike}
        togglingLikeId={togglingLikeId}
        entities={entities}
        sceneState={sceneState}
      />
    );
  }

  if (type === "DICE_ROLL") {
    const characterName = resolveDiceRollCharacterName(
      message,
      members,
      entities,
      sceneState,
      isMaster,
    );
    const playerName = resolvePlayerName(message, members);
    const avatarUrl = resolveMessageAvatarUrl(message, entities);
    return (
      <DiceRollCard
        message={message}
        characterName={characterName}
        playerName={playerName}
        avatarUrl={avatarUrl}
        timestamp={formatChatTimestamp(message.timestamp)}
        isOwn={message.sender_id === currentUserId}
        isMaster={isMaster}
        onDelete={onDelete}
        onToggleLike={onToggleLike}
        togglingLikeId={togglingLikeId}
        currentUserId={currentUserId}
        members={members}
        entities={entities}
      />
    );
  }

  const isOwn = message.sender_id === currentUserId;
  const characterName = resolveCharacterName(message, members, type);
  const playerName = resolvePlayerName(message, members);
  const masterVoice = isMasterVoice(message, members, type);
  const avatarUrl = resolveMessageAvatarUrl(message, entities);
  const meta = MESSAGE_TYPE_META[type] ?? MESSAGE_TYPE_META.ACTION;
  const masterOnly = isMaster && isMasterOnlyMessage(message);
  const readBy = message.read_by ?? [];
  const readersExcludingSender = readBy.filter((id) => id !== message.sender_id);
  const unreadCount = Math.max(memberCount - 1 - readersExcludingSender.length, 0);

  function handleDeleteClick() {
    if (!message.id || !onDelete) return;
    onDelete(message.id);
  }

  return (
    <article
      className={`chat-card ${isOwn ? "chat-card--own" : ""} ${masterVoice ? "chat-card--master" : ""} chat-card--${meta.color}${masterOnly ? " chat-card--master-only" : ""}`}
    >
      <header className="chat-card__header">
        <div className="chat-card__identity">
          <ChatAvatar name={characterName} avatarUrl={avatarUrl} />
          <div className="chat-card__identity-text">
            <span className="chat-card__character-row">
              <strong className="chat-card__character">{characterName}</strong>
              <ChatIllustrationPreviewIcon message={message} entities={entities} isMaster={isMaster} />
            </span>
            <span className={`chat-card__type chat-card__type--${meta.color}`}>{meta.label}</span>
            {masterOnly && <MasterOnlyMessageBadge message={message} />}
          </div>
        </div>
        <div className="chat-card__meta">
          {isMaster && message.id && onDelete && (
            <ChatMessageDeleteButton onClick={handleDeleteClick} />
          )}
          <span className="chat-card__player">{playerName}</span>
          <time className="chat-card__time">{formatChatTimestamp(message.timestamp)}</time>
        </div>
      </header>
      <p className="chat-card__body">{message.text}</p>
      <footer className="chat-card__footer">
        <Tooltip content={buildReadTooltip(readBy, members)}>
          <span className="chat-card__read" aria-label={buildReadTooltip(readBy, members)}>
            <Eye size={13} aria-hidden />
            {readersExcludingSender.length}/{Math.max(memberCount - 1, 0)} leído
            {unreadCount > 0 && ` · ${unreadCount} pendiente`}
          </span>
        </Tooltip>
      </footer>
      <MessageLikeBadge
        messageId={message.id}
        likeCount={message.like_count}
        likedByUserIds={message.liked_by_user_ids}
        currentUserId={currentUserId}
        members={members}
        onToggle={onToggleLike}
        toggling={togglingLikeId === message.id}
      />
    </article>
  );
}

function resolveDiceRollCharacterName(
  message: ChatMessage,
  members: MemberLookup,
  entities?: CampaignEntity[],
  sceneState?: SceneStateInput | null,
  isMaster = false,
): string {
  if (message.speaker_display_name?.trim()) {
    return message.speaker_display_name.trim();
  }

  const storedName = message.entity_name?.trim();
  const resolvedFromEntity = resolveCombatEntityName(
    message.entity_id,
    storedName,
    entities,
    sceneState,
    isMaster,
  );
  if (resolvedFromEntity !== "Desconocido") {
    return resolvedFromEntity;
  }

  const sender = members[message.sender_id];
  if (sender?.role === "MASTER" || message.speaker_type === "MASTER") {
    return MASTER_DICE_ROLL_NAME;
  }
  return FALLBACK_CHARACTER_NAME;
}

function buildReadTooltip(readBy: string[], members: MemberLookup): string {
  if (readBy.length === 0) return "Nadie ha leído aún";
  return readBy.map((id) => members[id]?.display_name ?? id.slice(0, 8)).join(", ");
}
