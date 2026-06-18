import type { ChatMessage } from "../../api/types";
import { ChatMessageDeleteButton } from "./ChatMessageDeleteButton";
import { MESSAGE_TYPE_META, getInitials } from "./messageTypes";

type DiceRollCardProps = {
  message: ChatMessage;
  characterName: string;
  playerName: string;
  timestamp: string;
  isOwn: boolean;
  isMaster?: boolean;
  onDelete?: (messageId: string) => void;
};

export function DiceRollCard({
  message,
  characterName,
  playerName,
  timestamp,
  isOwn,
  isMaster = false,
  onDelete,
}: DiceRollCardProps) {
  const expression = message.dice_expression ?? message.roll_details?.expression?.toString() ?? "?";
  const raw = message.raw_result ?? message.final_result ?? 0;
  const final = message.final_result ?? raw;
  const modifierMatch = expression.match(/([+-]\d+)$/);
  const modifier = modifierMatch ? Number(modifierMatch[1]) : 0;
  const baseExpr = modifierMatch ? expression.replace(modifierMatch[0], "").trim() : expression;
  const meta = MESSAGE_TYPE_META.DICE_ROLL;

  function handleDeleteClick() {
    if (!message.id || !onDelete) return;
    onDelete(message.id);
  }

  return (
    <article className={`chat-card dice-roll-card ${isOwn ? "chat-card--own" : ""} chat-card--${meta.color}`}>
      <header className="chat-card__header">
        <div className="chat-card__identity">
          <span className="chat-card__avatar" aria-hidden>
            {getInitials(characterName)}
          </span>
          <div className="chat-card__identity-text">
            <strong className="chat-card__character">{characterName}</strong>
            <span className={`chat-card__type chat-card__type--${meta.color}`}>{meta.label}</span>
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

      <div className="dice-card__stage">
        <div className="dice-card__die" aria-hidden>
          <span className="dice-card__face">{raw}</span>
        </div>
        {modifier !== 0 && (
          <span className="dice-card__modifier">{modifier > 0 ? `+ ${modifier}` : modifier}</span>
        )}
        <span className="dice-card__total">{final}</span>
      </div>
      <p className="dice-card__formula">
        {baseExpr}
        {modifier !== 0 ? ` ${modifier > 0 ? "+" : ""}${modifier}` : ""} = {final}
      </p>
      {message.skill_checked && <p className="muted dice-card__skill">{message.skill_checked}</p>}
      {message.chat_summary && !message.skill_checked && (
        <p className="muted dice-card__skill">{message.chat_summary}</p>
      )}
    </article>
  );
}
