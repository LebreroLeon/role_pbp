import { ThumbsUp } from "lucide-react";
import type { MouseEvent } from "react";
import type { MemberLookup } from "./ChatEntry";

type MessageLikeBadgeProps = {
  messageId?: string;
  likeCount?: number;
  likedByUserIds?: string[];
  currentUserId: string;
  members: MemberLookup;
  onToggle?: (messageId: string) => void;
  toggling?: boolean;
};

function buildLikeTooltip(likedByUserIds: string[], members: MemberLookup): string {
  if (likedByUserIds.length === 0) return "Dar me gusta";
  return likedByUserIds.map((id) => members[id]?.display_name ?? id.slice(0, 8)).join(", ");
}

export function MessageLikeBadge({
  messageId,
  likeCount = 0,
  likedByUserIds = [],
  currentUserId,
  members,
  onToggle,
  toggling = false,
}: MessageLikeBadgeProps) {
  if (!messageId || !onToggle) return null;

  const resolvedMessageId = messageId;
  const toggleLike = onToggle;
  const userHasLiked = likedByUserIds.includes(currentUserId);
  const showBadge = likeCount > 0 || userHasLiked;

  function handleClick(event: MouseEvent<HTMLButtonElement>) {
    event.stopPropagation();
    if (toggling) return;
    toggleLike(resolvedMessageId);
  }

  return (
    <button
      type="button"
      className={`chat-card__like ${showBadge ? "chat-card__like--visible" : "chat-card__like--hint"} ${userHasLiked ? "chat-card__like--active" : ""}`}
      onClick={handleClick}
      disabled={toggling}
      title={buildLikeTooltip(likedByUserIds, members)}
      aria-label={userHasLiked ? "Quitar me gusta" : "Dar me gusta"}
      aria-pressed={userHasLiked}
    >
      <ThumbsUp
        size={13}
        strokeWidth={2}
        className="chat-card__like-icon"
        fill={userHasLiked ? "currentColor" : "none"}
        aria-hidden
      />
      {likeCount > 0 && <span className="chat-card__like-count">{likeCount}</span>}
    </button>
  );
}
