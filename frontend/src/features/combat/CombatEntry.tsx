import type { CampaignEntity, ChatMessage } from "../../api/types";
import type { MemberLookup } from "../scene/ChatEntry";
import { ChatIllustrationPreviewIcon } from "../scene/ChatIllustrationPreviewIcon";
import { ChatMessageDeleteButton } from "../scene/ChatMessageDeleteButton";
import { resolveEntityAvatarUrl } from "../entities/entityAvatar";
import { ChatAvatar } from "../scene/ChatAvatar";
import { MessageLikeBadge } from "../scene/MessageLikeBadge";
import { formatChatTimestamp } from "../scene/messageTypes";
import type { SceneStateInput } from "../scene/sceneState";
import { formatAttackRollLine, formatDamageLine, formatSaveDamageTakenLine, CRITICAL_MARKER } from "../scene/rollFormat";
import {
  resolveCombatEntityName,
  resolveCombatEvent,
  resolveCombatSpeakerEntityId,
} from "./combatMessage";
import { MasterOnlyMessageBadge } from "../scene/MasterOnlyMessageBadge";
import { isMasterOnlyMessage } from "../scene/messageVisibility";

const FALLBACK_NARRATOR_NAME = "Máster / Narrador";

type CombatEntryProps = {
  message: ChatMessage;
  members: MemberLookup;
  currentUserId: string;
  isMaster?: boolean;
  onDelete?: (messageId: string) => void;
  onToggleLike?: (messageId: string) => void;
  togglingLikeId?: string | null;
  entities?: CampaignEntity[];
  sceneState?: SceneStateInput | null;
};

export function CombatEntry({
  message,
  members,
  currentUserId,
  isMaster = false,
  onDelete,
  onToggleLike,
  togglingLikeId = null,
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
  const masterOnly = isMaster && isMasterOnlyMessage(message);
  const cardClassName = `chat-card combat-card ${isOwn ? "chat-card--own combat-card--own" : ""}${masterOnly ? " chat-card--master-only" : ""}`;

  const likeBadge = (
    <MessageLikeBadge
      messageId={message.id}
      likeCount={message.like_count}
      likedByUserIds={message.liked_by_user_ids}
      currentUserId={currentUserId}
      members={members}
      onToggle={onToggleLike}
      toggling={togglingLikeId === message.id}
    />
  );

  if (!event) {
    return (
      <article className={cardClassName}>
        <header className="chat-card__header">
          <div className="chat-card__identity">
            <ChatAvatar name={characterName} avatarUrl={avatarUrl} />
            <div className="chat-card__identity-text">
              <span className="chat-card__character-row">
                <strong className="chat-card__character">{characterName}</strong>
                <ChatIllustrationPreviewIcon
                  entityId={speakerEntityId}
                  entities={entities}
                  isMaster={isMaster}
                />
              </span>
              <span className="chat-card__type chat-card__type--action">Combate</span>
              {masterOnly && <MasterOnlyMessageBadge message={message} />}
            </div>
          </div>
          <div className="chat-card__meta">
            {deleteButton}
            <span className="chat-card__player">{playerName}</span>
            <time className="chat-card__time">{timestamp}</time>
          </div>
        </header>
        <p className="chat-card__body">{summary ?? "Evento de combate"}</p>
        {likeBadge}
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
  const isHealing = Boolean(event.is_healing || damage?.is_healing);
  const isSaveAttack = attackRoll?.resolution === "save" || attackRoll?.save_dc != null;
  const isCritical = Boolean(
    event.is_critical || attackRoll?.is_critical || attackRoll?.natural_20 || damage?.is_critical,
  );
  const isSheetRoll = message.type === "DICE_ROLL";
  const isSceneCombat = message.type === "COMBAT";
  const showStructuredCombat =
    event.kind === "ATTACK_RESOLVED" || (event.kind === "DAMAGE_APPLIED" && isSheetRoll);
  const targetAc = attackRoll?.target_ac;
  const weaponLabel = event.weapon_name?.trim() || undefined;
  const actionHeader = buildCombatActionHeader({
    attackerLabel,
    defenderLabel: isSceneCombat ? defenderLabel : undefined,
    weaponLabel,
    targetAc,
    isSheetRoll,
    isHealing,
    isSaveAttack,
  });
  const hpRemaining = event.defender_hp_remaining ?? event.hp?.after;
  const hpBefore = event.hp?.before;
  const hpLabel = formatHp(hpRemaining, event.defender_hp_max);
  const damageLine = damage
    ? isHealing
      ? formatDamageLine({ ...damage, is_healing: true })
      : isSaveAttack
        ? formatSaveDamageTakenLine(defenderLabel, damage)
        : formatDamageLine(damage)
    : null;
  const attackLineIncludesCritical = Boolean(
    attackRoll?.chat_summary?.includes(CRITICAL_MARKER) ||
      (attackRoll && formatAttackRollLine(attackRoll).includes(CRITICAL_MARKER)),
  );
  const damageLineIncludesCritical =
    Boolean(damage?.chat_summary?.includes(CRITICAL_MARKER)) ||
    Boolean(damageLine?.includes(CRITICAL_MARKER));

  return (
    <article className={cardClassName} aria-label="Combate">
      <header className="chat-card__header">
        <div className="chat-card__identity">
          <ChatAvatar name={characterName} avatarUrl={avatarUrl} />
          <div className="chat-card__identity-text">
            <span className="chat-card__character-row">
              <strong className="chat-card__character">{characterName}</strong>
              <ChatIllustrationPreviewIcon
                entityId={speakerEntityId}
                entities={entities}
                isMaster={isMaster}
              />
            </span>
            <span className="chat-card__type chat-card__type--action">Combate</span>
            {masterOnly && <MasterOnlyMessageBadge message={message} />}
          </div>
        </div>
        <div className="chat-card__meta">
          {deleteButton}
          <span className="chat-card__player">{playerName}</span>
          <time className="chat-card__time">{timestamp}</time>
        </div>
      </header>

      {showStructuredCombat && actionHeader ? (
        <p className="combat-card__action">{actionHeader}</p>
      ) : summary ? (
        <p className="chat-card__body">{summary}</p>
      ) : null}

      {attackRoll && !isHealing && (
        <p className="combat-card__roll-line">
          {formatAttackRollLine(attackRoll)}
          {attackRoll.natural_1 && (
            <span className="combat-card__crit combat-card__crit--fail"> — Fallo automático</span>
          )}
          {isCritical && !attackRoll.natural_1 && !attackLineIncludesCritical && (
            <span className="combat-card__crit"> — {CRITICAL_MARKER}</span>
          )}
        </p>
      )}

      {damage && damage.amount > 0 && damageLine && (
        <p className="combat-card__roll-line combat-card__damage-line">
          {damageLine}
          {isCritical && !isHealing && !damageLineIncludesCritical && (
            <span className="combat-card__crit"> — {CRITICAL_MARKER}</span>
          )}
        </p>
      )}

      {event.is_instant_death && (
        <p className="combat-card__crit">Muerte instantánea</p>
      )}

      {event.death_save_failures_added ? (
        <p className="combat-card__summary muted">
          +{event.death_save_failures_added} fallo(s) de salvación contra la muerte
        </p>
      ) : null}

      {hpLabel && (
        <p className="combat-card__hp">
          PV {hpBefore != null ? `${hpBefore} → ` : ""}
          <strong>{hpLabel}</strong>
          {defenderLabel && <span className="muted"> ({defenderLabel})</span>}
        </p>
      )}

      {summary && !showStructuredCombat && (
        <p className="combat-card__summary muted">{summary}</p>
      )}
      {likeBadge}
    </article>
  );
}

function formatHp(current?: number, max?: number): string | null {
  if (current == null) return null;
  if (max != null) return `${current}/${max}`;
  return String(current);
}

function buildCombatActionHeader({
  attackerLabel,
  defenderLabel,
  weaponLabel,
  targetAc,
  isSheetRoll,
  isHealing,
  isSaveAttack,
}: {
  attackerLabel: string;
  defenderLabel?: string;
  weaponLabel?: string;
  targetAc?: number;
  isSheetRoll: boolean;
  isHealing: boolean;
  isSaveAttack: boolean;
}): string | null {
  if (!attackerLabel) return null;

  const attackerPart = weaponLabel ? `${attackerLabel} (${weaponLabel})` : attackerLabel;
  if (isSheetRoll || !defenderLabel) {
    return `${attackerPart} ataca...`;
  }

  const verb = isHealing ? "cura a" : isSaveAttack ? "lanza contra" : "ataca";
  const targetPart =
    !isHealing && !isSaveAttack && targetAc != null
      ? `${defenderLabel} (CA ${targetAc})`
      : defenderLabel;
  return `${attackerPart} ${verb} ${targetPart}`;
}
