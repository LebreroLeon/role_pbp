import type { CampaignEntity, ChatMessage } from "../../api/types";
import type { MemberLookup } from "./ChatEntry";
import { ChatIllustrationPreviewIcon } from "./ChatIllustrationPreviewIcon";
import { ChatMessageDeleteButton } from "./ChatMessageDeleteButton";
import { ChatAvatar } from "./ChatAvatar";
import { MESSAGE_TYPE_META } from "./messageTypes";
import { MessageLikeBadge } from "./MessageLikeBadge";
import {
  formatModifierBreakdownLine,
  formatRollSummaryLine,
  parseModifierBreakdown,
  resolveRollDice,
  resolveRollLabel,
} from "./rollFormat";
import { MasterOnlyMessageBadge } from "./MasterOnlyMessageBadge";
import { isMasterOnlyMessage } from "./messageVisibility";

type DiceRollCardProps = {
  message: ChatMessage;
  characterName: string;
  playerName: string;
  avatarUrl?: string;
  timestamp: string;
  isOwn: boolean;
  isMaster?: boolean;
  onDelete?: (messageId: string) => void;
  onToggleLike?: (messageId: string) => void;
  togglingLikeId?: string | null;
  currentUserId: string;
  members: MemberLookup;
  entities?: CampaignEntity[];
};

export function DiceRollCard({
  message,
  characterName,
  playerName,
  avatarUrl,
  timestamp,
  isOwn,
  isMaster = false,
  onDelete,
  onToggleLike,
  togglingLikeId = null,
  currentUserId,
  members,
  entities,
}: DiceRollCardProps) {
  const rollLabel = resolveRollLabel(message);
  const dice = resolveRollDice(message);
  const modifierBreakdown = parseModifierBreakdown(message.roll_details);
  const breakdownLine = formatModifierBreakdownLine(modifierBreakdown);
  const summaryLine = formatRollSummaryLine(message);
  const final = message.final_result ?? message.raw_result ?? 0;
  const natural =
    typeof message.roll_details?.natural_roll === "number"
      ? message.roll_details.natural_roll
      : dice[dice.length - 1] ?? final;
  const meta = MESSAGE_TYPE_META.DICE_ROLL;
  const masterOnly = isMaster && isMasterOnlyMessage(message);

  function handleDeleteClick() {
    if (!message.id || !onDelete) return;
    onDelete(message.id);
  }

  return (
    <article
      className={`chat-card dice-roll-card ${isOwn ? "chat-card--own" : ""} chat-card--${meta.color}${masterOnly ? " chat-card--master-only" : ""}`}
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
          <time className="chat-card__time">{timestamp}</time>
        </div>
      </header>

      {rollLabel && <p className="dice-card__roll-label">{rollLabel}</p>}

      <div className="dice-card__stage">
        {dice.length > 1 ? (
          <div className="dice-card__dice-group" aria-hidden>
            {dice.map((value, index) => (
              <div key={`${value}-${index}`} className="dice-card__die dice-card__die--small">
                <span
                  className={`dice-card__face${
                    value === natural ? " dice-card__face--chosen" : ""
                  }`}
                >
                  {value}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div className="dice-card__die" aria-hidden>
            <span className="dice-card__face">{natural}</span>
          </div>
        )}
        <span className="dice-card__total">{final}</span>
      </div>

      <p className="combat-card__roll-line dice-card__formula">{summaryLine}</p>

      {breakdownLine && <p className="dice-card__breakdown muted">{breakdownLine}</p>}

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
