import type { ChatMessage, CombatAttackRollSummary, CombatDamageSummary } from "../../api/types";
import { damageTypeLabel } from "../character-sheet/systems/dnd5e/damageTypes";

export type ModifierBreakdownEntry = {
  label: string;
  value: number;
  rolls?: number[];
  expression?: string;
};

export function parseModifierBreakdown(details: Record<string, unknown> | undefined): ModifierBreakdownEntry[] {
  if (!details) return [];
  const raw = details.modifier_breakdown;
  if (!Array.isArray(raw)) return [];

  const entries: ModifierBreakdownEntry[] = [];
  for (const entry of raw) {
    if (!entry || typeof entry !== "object") continue;
    const record = entry as Record<string, unknown>;
    const label = typeof record.label === "string" ? record.label : "";
    const value = typeof record.value === "number" ? record.value : 0;
    if (!label) continue;
    const parsed: ModifierBreakdownEntry = { label, value };
    if (Array.isArray(record.rolls)) {
      parsed.rolls = record.rolls.filter((roll): roll is number => typeof roll === "number");
    }
    if (typeof record.expression === "string") {
      parsed.expression = record.expression;
    }
    entries.push(parsed);
  }
  return entries;
}

export function resolveRollLabel(message: ChatMessage): string | null {
  const details = message.roll_details;
  if (details && typeof details.roll_label === "string" && details.roll_label.trim()) {
    return details.roll_label.trim();
  }
  if (message.skill_checked?.trim()) return message.skill_checked.trim();
  if (message.roll_type) {
    return message.roll_type.replace(/_/g, " ");
  }
  return null;
}

export function resolveRollDice(message: ChatMessage): number[] {
  if (Array.isArray(message.rolls) && message.rolls.length > 0) {
    return message.rolls;
  }
  const detailsRolls = message.roll_details?.rolls;
  if (Array.isArray(detailsRolls)) {
    return detailsRolls.filter((roll): roll is number => typeof roll === "number");
  }
  if (typeof message.roll_details?.natural_roll === "number") {
    return [message.roll_details.natural_roll];
  }
  if (typeof message.raw_result === "number") {
    return [message.raw_result];
  }
  return [];
}

export function formatModifierValue(value: number): string {
  if (value > 0) return `+${value}`;
  return String(value);
}

export function formatModifierBreakdownLine(entries: ModifierBreakdownEntry[]): string | null {
  const parts = entries
    .filter((entry) => entry.value !== 0 || (entry.rolls?.length ?? 0) > 0)
    .map((entry) => {
      if (entry.rolls?.length) {
        const diceText =
          entry.rolls.length === 1
            ? entry.label.includes("=")
              ? entry.label
              : `${entry.label}=${entry.rolls[0]}`
            : `[${entry.rolls.join(", ")}]`;
        return diceText;
      }
      return `${entry.label} ${formatModifierValue(entry.value)}`;
    });
  return parts.length > 0 ? parts.join(" · ") : null;
}

const PLACEHOLDER_DAMAGE_TYPES = new Set(["sin tipo", "untyped", "sintype", "unknown"]);

export const CRITICAL_MARKER = "¡CRÍTICO!";

function formatModifierSuffix(modifier: number): string {
  if (modifier > 0) return `+${modifier}`;
  if (modifier < 0) return String(modifier);
  return "";
}

function formatNaturalPlusModifier(natural: number, modifier: number): string {
  if (modifier) return `${natural}${modifier > 0 ? `+${modifier}` : modifier}`;
  return String(natural);
}

function formatDiceRollsSum(rolls: number[]): string {
  if (!rolls.length) return "?";
  return rolls.join("+");
}

function resolveDamageTypeLabel(type?: string): string | null {
  if (!type?.trim()) return null;
  if (PLACEHOLDER_DAMAGE_TYPES.has(type.trim().toLowerCase())) return null;
  const label = damageTypeLabel(type);
  return label === type ? null : label;
}

export function formatSaveDamageTakenLine(
  defenderName: string,
  damage: CombatDamageSummary,
): string {
  const amount = damage.modified_amount ?? damage.amount;
  const typeLabel = resolveDamageTypeLabel(damage.type);
  if (typeLabel) {
    return `${defenderName} pierde ${amount} PV de ${typeLabel}`;
  }
  return `${defenderName} pierde ${amount} PV`;
}

const D20_ROLL_TYPES = new Set([
  "ability_check",
  "saving_throw",
  "skill_check",
  "attack_roll",
  "attack",
  "initiative",
]);

function isContextualD20Roll(message: ChatMessage, dice: number[]): boolean {
  const details = message.roll_details ?? {};
  const rollType = message.roll_type?.toLowerCase();
  if (rollType && D20_ROLL_TYPES.has(rollType)) return true;
  if (details.advantage || details.disadvantage) return true;
  if (typeof details.natural_roll === "number") return true;
  const expression = message.dice_expression ?? "";
  if (dice.length === 1 && /d20/i.test(expression)) return true;
  return false;
}

export function formatRollSummaryLine(message: ChatMessage): string {
  if (message.chat_summary?.trim()) {
    return message.chat_summary.trim();
  }

  const label = resolveRollLabel(message);
  const dice = resolveRollDice(message);
  const details = message.roll_details ?? {};
  const modifier = typeof details.modifier === "number" ? details.modifier : 0;
  const total = message.final_result ?? message.raw_result ?? 0;
  const natural =
    typeof details.natural_roll === "number" ? details.natural_roll : dice[dice.length - 1];

  let diceLabel = "1d20";
  if (details.advantage) diceLabel = "2d20 (ventaja)";
  else if (details.disadvantage) diceLabel = "2d20 (desventaja)";

  const prefix = label ? `${label}: ` : "";

  if (natural != null && isContextualD20Roll(message, dice)) {
    let line = `${prefix}${diceLabel}=${natural}`;
    if (modifier) line += ` ${formatModifierValue(modifier)}`;
    line += ` = ${total}`;
    if (typeof details.dc === "number") {
      line += ` vs CD ${details.dc}`;
      if (message.success != null) {
        line += ` — ${message.success ? "éxito" : "fallo"}`;
      }
    }
    if (typeof details.target_ac === "number") {
      line += ` vs CA ${details.target_ac}`;
      if (typeof details.hit === "boolean") {
        line += ` — ${details.hit ? "Impacto" : "Fallo"}`;
      }
    }
    return line;
  }

  const expression = message.dice_expression ?? message.roll_details?.expression?.toString() ?? "?";
  const diceSum = dice.reduce((sum, value) => sum + value, 0);
  const miscMod = modifier || total - diceSum;

  if (dice.length > 1) {
    let line = `${prefix}${dice.join(" + ")}`;
    if (miscMod) line += ` ${formatModifierValue(miscMod)}`;
    return `${line} = ${total}`;
  }

  if (dice.length === 1) {
    const baseExpr = expression.replace(/[+-]\d+$/, "").trim();
    let line = `${prefix}${baseExpr}=${dice[0]}`;
    if (miscMod) line += ` ${formatModifierValue(miscMod)}`;
    return `${line} = ${total}`;
  }

  return `${prefix}${expression} = ${total}`;
}

export function formatAttackRollLine(attackRoll: CombatAttackRollSummary): string {
  if (attackRoll.chat_summary?.trim()) {
    return attackRoll.chat_summary.trim();
  }

  const modifier = attackRoll.modifier ?? 0;
  const rolls = attackRoll.rolls ?? [];
  const natural = rolls[rolls.length - 1] ?? attackRoll.total - modifier;
  const modSuffix = formatModifierSuffix(modifier);
  const breakdown = formatNaturalPlusModifier(natural, modifier);
  let line = `Ataque: 1d20${modSuffix} = ${breakdown} = ${attackRoll.total}`;

  if (attackRoll.save_dc != null) {
    line += ` vs CD ${attackRoll.save_dc}`;
    if (attackRoll.save_succeeded != null) {
      line += attackRoll.save_succeeded ? " — salvación superada" : " — salvación fallida";
    }
  } else if (attackRoll.target_ac != null) {
    line += ` vs CA ${attackRoll.target_ac}`;
    if (attackRoll.hit != null) {
      line += ` — ${attackRoll.hit ? "Impacto" : "Fallo"}`;
    }
  } else if (attackRoll.hit != null) {
    line += ` — ${attackRoll.hit ? "Impacto" : "Fallo"}`;
  }

  const isCritical = Boolean(
    attackRoll.is_critical || attackRoll.natural_20,
  );
  if (isCritical && attackRoll.hit !== false) {
    line += ` — ${CRITICAL_MARKER}`;
  }
  return line;
}

export function formatDamageLine(damage: CombatDamageSummary): string {
  if (damage.chat_summary?.trim()) {
    return damage.chat_summary.trim();
  }

  const rawAmount = damage.raw_amount;
  const modifiedAmount = damage.modified_amount ?? damage.amount;
  const modifierLabel = damage.damage_modifier;
  const typeLabel = resolveDamageTypeLabel(damage.type);

  if (
    rawAmount != null &&
    modifierLabel &&
    rawAmount !== modifiedAmount &&
    typeLabel
  ) {
    return `Daño: ${rawAmount} ${typeLabel} → ${modifiedAmount} (${modifierLabel})`;
  }

  const rolls = damage.rolls ?? [];
  const modifier = damage.modifier ?? 0;
  const expression = damage.expression ?? "?";
  const rollsPart = formatDiceRollsSum(rolls);
  const breakdown =
    modifier && rollsPart !== "?"
      ? `${rollsPart}${modifier > 0 ? `+${modifier}` : modifier}`
      : rollsPart;
  const label = damage.is_healing ? "Curación" : "Daño";
  let line = `${label}: ${expression} = ${breakdown} = ${modifiedAmount}`;
  if (typeLabel) {
    line += ` ${typeLabel}`;
  }
  if (damage.is_critical) {
    line += ` — ${CRITICAL_MARKER}`;
  }
  return line;
}

export function formatDamageType(type?: string): string {
  return resolveDamageTypeLabel(type) ?? "";
}
