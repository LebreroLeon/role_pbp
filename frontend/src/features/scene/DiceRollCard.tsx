import type { ChatMessage } from "../../api/types";

type DiceRollCardProps = {
  message: ChatMessage;
  senderName: string;
  timestamp: string;
  isOwn: boolean;
};

export function DiceRollCard({ message, senderName, timestamp, isOwn }: DiceRollCardProps) {
  const expression = message.dice_expression ?? "?";
  const raw = message.raw_result ?? message.final_result ?? 0;
  const final = message.final_result ?? raw;
  const modifierMatch = expression.match(/([+-]\d+)$/);
  const modifier = modifierMatch ? Number(modifierMatch[1]) : 0;
  const baseExpr = modifierMatch ? expression.replace(modifierMatch[0], "").trim() : expression;

  return (
    <article className={`dice-card ${isOwn ? "dice-card--own" : ""}`}>
      <header className="dice-card__header">
        <strong>{senderName}</strong>
        <time>{timestamp}</time>
      </header>
      <div className="dice-card__stage">
        <div className="dice-card__die" aria-hidden>
          <span className="dice-card__face">{raw}</span>
        </div>
        {modifier !== 0 && <span className="dice-card__modifier">{modifier > 0 ? `+ ${modifier}` : modifier}</span>}
        <span className="dice-card__total">{final}</span>
      </div>
      <p className="dice-card__formula">
        {baseExpr}
        {modifier !== 0 ? ` ${modifier > 0 ? "+" : ""}${modifier}` : ""} = {final}
      </p>
      {message.skill_checked && <p className="muted dice-card__skill">{message.skill_checked}</p>}
    </article>
  );
}
