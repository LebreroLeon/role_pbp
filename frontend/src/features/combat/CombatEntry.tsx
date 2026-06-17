import type { ChatMessage } from "../../api/types";
import type { MemberLookup } from "../scene/ChatEntry";
import { formatChatTimestamp } from "../scene/messageTypes";
import {
  formatDamageType,
  resolveCombatEvent,
} from "./combatMessage";

type CombatEntryProps = {
  message: ChatMessage;
  members: MemberLookup;
  currentUserId: string;
};

export function CombatEntry({ message, members, currentUserId }: CombatEntryProps) {
  const event = resolveCombatEvent(message);
  const isOwn = message.sender_id === currentUserId;
  const senderName = members[message.sender_id]?.display_name ?? message.sender_id.slice(0, 8);
  const timestamp = formatChatTimestamp(message.timestamp);
  const summary = message.chat_summary ?? message.text;

  if (!event) {
    return (
      <article className={`combat-card ${isOwn ? "combat-card--own" : ""}`}>
        <header className="combat-card__header">
          <strong>{senderName}</strong>
          <time>{timestamp}</time>
        </header>
        <p className="combat-card__summary">{summary ?? "Evento de combate"}</p>
      </article>
    );
  }

  const attackerLabel = event.attacker_name ?? labelEntity(event.attacker_id);
  const defenderLabel = event.defender_name ?? labelEntity(event.defender_id);
  const attackRoll = event.attack_roll;
  const damage = event.damage;
  const hpLabel = formatHp(event.defender_hp_remaining, event.defender_hp_max);

  return (
    <article className={`combat-card ${isOwn ? "combat-card--own" : ""}`} aria-label="Combate">
      <header className="combat-card__header">
        <div className="combat-card__identity">
          <span className="combat-card__badge">Combate</span>
          <strong>{senderName}</strong>
        </div>
        <time>{timestamp}</time>
      </header>

      {event.kind === "ATTACK_RESOLVED" && attackerLabel && defenderLabel ? (
        <p className="combat-card__action">
          <span className="combat-card__entity">{attackerLabel}</span>
          <span className="combat-card__verb">ataca</span>
          <span className="combat-card__entity combat-card__entity--target">{defenderLabel}</span>
          {event.weapon_name && <span className="combat-card__weapon">({event.weapon_name})</span>}
        </p>
      ) : summary ? (
        <p className="combat-card__summary">{summary}</p>
      ) : null}

      {attackRoll && (
        <div className="combat-card__roll">
          <span className="combat-card__roll-label">Ataque</span>
          <span className="combat-card__roll-total">{attackRoll.total}</span>
          {attackRoll.target_ac != null && (
            <span className="combat-card__roll-vs">vs CA {attackRoll.target_ac}</span>
          )}
          {attackRoll.hit != null && (
            <span
              className={`combat-card__hit ${attackRoll.hit ? "combat-card__hit--success" : "combat-card__hit--fail"}`}
            >
              {attackRoll.hit ? "Impacto" : "Fallo"}
            </span>
          )}
          {attackRoll.natural_20 && <span className="combat-card__crit">¡Crítico!</span>}
          {attackRoll.natural_1 && <span className="combat-card__crit combat-card__crit--fail">Fallo crítico</span>}
        </div>
      )}

      {damage && damage.amount > 0 && (
        <div className="combat-card__damage">
          <span className="combat-card__damage-label">Daño</span>
          <span className="combat-card__damage-amount">{damage.amount}</span>
          {damage.type && (
            <span className="combat-card__damage-type">{formatDamageType(damage.type)}</span>
          )}
        </div>
      )}

      {hpLabel && (
        <p className="combat-card__hp">
          PV restantes: <strong>{hpLabel}</strong>
          {defenderLabel && <span className="muted"> ({defenderLabel})</span>}
        </p>
      )}

      {summary && event.kind !== "ATTACK_RESOLVED" && (
        <p className="combat-card__summary muted">{summary}</p>
      )}
    </article>
  );

  function labelEntity(entityId?: string): string | null {
    if (!entityId) return null;
    return entityId.slice(0, 8);
  }
}

function formatHp(current?: number, max?: number): string | null {
  if (current == null) return null;
  if (max != null) return `${current}/${max}`;
  return String(current);
}
