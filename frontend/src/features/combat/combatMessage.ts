import type { ChatMessage, CombatEvent } from "../../api/types";

const COMBAT_ROLL_TYPES = new Set(["attack", "attack_roll", "damage", "initiative"]);

export function isCombatMessage(message: ChatMessage): boolean {
  return message.type === "COMBAT" || Boolean(message.combat_event);
}

export function isCombatEnrichedDiceRoll(message: ChatMessage): boolean {
  if (message.type !== "DICE_ROLL") return false;
  if (message.combat_event) return true;

  const rollType = message.roll_type?.toLowerCase();
  if (rollType && COMBAT_ROLL_TYPES.has(rollType)) return true;

  const details = message.roll_details;
  if (!details) return false;

  return (
    "hit" in details ||
    "target_ac" in details ||
    "damage_type" in details ||
    "defender_hp_remaining" in details
  );
}

export function shouldRenderCombatEntry(message: ChatMessage): boolean {
  return isCombatMessage(message) || isCombatEnrichedDiceRoll(message);
}

export function resolveCombatEvent(message: ChatMessage): CombatEvent | null {
  if (message.combat_event) return message.combat_event;

  if (message.type === "COMBAT" || isCombatEnrichedDiceRoll(message)) {
    const details = message.roll_details ?? {};
    const rollType = message.roll_type?.toLowerCase();

    if (rollType === "damage" || details.damage_type != null) {
      return {
        kind: "DAMAGE_APPLIED",
        defender_id: message.entity_id,
        defender_name: message.entity_name ?? (details.defender_name as string | undefined),
        damage: {
          amount: message.final_result ?? (details.amount as number | undefined) ?? 0,
          type: (details.damage_type as string | undefined) ?? (details.type as string | undefined),
        },
        defender_hp_remaining: details.defender_hp_remaining as number | undefined,
        defender_hp_max: details.defender_hp_max as number | undefined,
      };
    }

    return {
      kind: "ATTACK_RESOLVED",
      attacker_id: message.entity_id,
      attacker_name: message.entity_name ?? (details.attacker_name as string | undefined),
      defender_id: details.defender_id as string | undefined,
      defender_name: details.defender_name as string | undefined,
      attack_roll: {
        total: message.final_result ?? 0,
        hit: details.hit as boolean | undefined,
        natural_20: details.natural_20 as boolean | undefined,
        natural_1: details.natural_1 as boolean | undefined,
        target_ac: details.target_ac as number | undefined,
        expression: message.dice_expression,
        rolls: message.roll_details?.rolls as number[] | undefined,
      },
      damage:
        details.damage_amount != null
          ? {
              amount: details.damage_amount as number,
              type: details.damage_type as string | undefined,
            }
          : undefined,
      defender_hp_remaining: details.defender_hp_remaining as number | undefined,
      defender_hp_max: details.defender_hp_max as number | undefined,
      weapon_name: details.attack_name as string | undefined,
    };
  }

  return null;
}

export function formatDamageType(type?: string): string {
  if (!type) return "";
  return type.replace(/_/g, " ");
}
