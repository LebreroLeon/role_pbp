import type { CampaignEntity, ChatMessage } from "../../api/types";
import type { MemberLookup } from "../scene/ChatEntry";
import { ChatMessageDeleteButton } from "../scene/ChatMessageDeleteButton";
import { resolveEntityAvatarUrl } from "../entities/entityAvatar";
import { ChatAvatar } from "../scene/ChatAvatar";
import { formatChatTimestamp } from "../scene/messageTypes";
import type { SceneStateInput } from "../scene/sceneState";
import {
  formatAttackRollLine,
  formatDamageType,
  resolveCombatEntityName,
  resolveCombatEvent,
  resolveCombatSpeakerEntityId,
} from "./combatMessage";

const FALLBACK_NARRATOR_NAME = "Máster / Narrador";

type CombatEntryProps = {
  message: ChatMessage;
  members: MemberLookup;
  currentUserId: string;
  isMaster?: boolean;
  onDelete?: (messageId: string) => void;
  entities?: CampaignEntity[];
  sceneState?: SceneStateInput | null;
};

export function CombatEntry({
  message,
  members,
  currentUserId,
  isMaster = false,
  onDelete,
  entities,
  sceneState,
}: CombatEntryProps) {
  const event = resolveCombatEvent(message);
  const isOwn = message.sender_id === currentUserId;
  const playerName = members[message.sender_id]?.display_name ?? "Desconocido";
  const timestamp = formatChatTimestamp(message.timestamp);
  const summary = message.chat_summary ?? message.text;

  function handleDeleteClick() {
    if (!message.id || !onDelete) return;
    onDelete(message.id);
  }

  const deleteButton =
    isMaster && message.id && onDelete ? (
      <ChatMessageDeleteButton onClick={handleDeleteClick} />
    ) : null;

  const speakerEntityId = event ? resolveCombatSpeakerEntityId(event) : message.entity_id;
  const storedSpeakerName =
    message.speaker_display_name ??
    (event?.kind === "ATTACK_RESOLVED"
      ? event.attacker_name
      : event?.kind === "DAMAGE_APPLIED"
        ? event.defender_name
        : message.entity_name);

  const characterName =
    message.speaker_display_name ??
    (speakerEntityId
      ? resolveCombatEntityName(
          speakerEntityId,
          storedSpeakerName,
          entities,
          sceneState,
          isMaster,
        )
      : storedSpeakerName?.trim() || FALLBACK_NARRATOR_NAME);

  const avatarUrl = resolveEntityAvatarUrl(speakerEntityId, entities);

  if (!event) {
    return (
      <article className={`chat-card combat-card ${isOwn ? "chat-card--own combat-card--own" : ""}`}>
        <header className="chat-card__header">
          <div className="chat-card__identity">
            <ChatAvatar name={characterName} avatarUrl={avatarUrl} />
            <div className="chat-card__identity-text">
              <strong className="chat-card__character">{characterName}</strong>
              <span className="chat-card__type chat-card__type--action">Combate</span>
            </div>
          </div>
          <div className="chat-card__meta">
            {deleteButton}
            <span className="chat-card__player">{playerName}</span>
            <time className="chat-card__time">{timestamp}</time>
          </div>
        </header>
        <p className="chat-card__body">{summary ?? "Evento de combate"}</p>
      </article>
    );
  }

  const attackerLabel = resolveCombatEntityName(
    event.attacker_id,
    event.attacker_name,
    entities,
    sceneState,
    isMaster,
  );
  const defenderLabel = resolveCombatEntityName(
    event.defender_id,
    event.defender_name,
    entities,
    sceneState,
    isMaster,
  );
  const attackRoll = event.attack_roll;
  const damage = event.damage;
  const hpRemaining = event.defender_hp_remaining ?? event.hp?.after;
  const hpBefore = event.hp?.before;
  const hpLabel = formatHp(hpRemaining, event.defender_hp_max);

  return (
    <article
      className={`chat-card combat-card ${isOwn ? "chat-card--own combat-card--own" : ""}`}
      aria-label="Combate"
    >
      <header className="chat-card__header">
        <div className="chat-card__identity">
          <ChatAvatar name={characterName} avatarUrl={avatarUrl} />
          <div className="chat-card__identity-text">
            <strong className="chat-card__character">{characterName}</strong>
            <span className="chat-card__type chat-card__type--action">Combate</span>
          </div>
        </div>
        <div className="chat-card__meta">
          {deleteButton}
          <span className="chat-card__player">{playerName}</span>
          <time className="chat-card__time">{timestamp}</time>
        </div>
      </header>

      {event.kind === "ATTACK_RESOLVED" && attackerLabel && defenderLabel ? (
        <p className="combat-card__action">
          <span className="combat-card__entity">{attackerLabel}</span>
          <span className="combat-card__verb">ataca</span>
          <span className="combat-card__entity combat-card__entity--target">{defenderLabel}</span>
          {event.weapon_name && <span className="combat-card__weapon">({event.weapon_name})</span>}
        </p>
      ) : summary ? (
        <p className="chat-card__body">{summary}</p>
      ) : null}

      {attackRoll && (
        <p className="combat-card__roll-line">{formatAttackRollLine(attackRoll)}</p>
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
          PV {hpBefore != null ? `${hpBefore} → ` : ""}
          <strong>{hpLabel}</strong>
          {defenderLabel && <span className="muted"> ({defenderLabel})</span>}
        </p>
      )}

      {summary && event.kind !== "ATTACK_RESOLVED" && (
        <p className="combat-card__summary muted">{summary}</p>
      )}
    </article>
  );
}

function formatHp(current?: number, max?: number): string | null {
  if (current == null) return null;
  if (max != null) return `${current}/${max}`;
  return String(current);
}
