import type { SheetRollContext, SheetRollType } from "../../api/types";

export type AdvantageMode = "normal" | "advantage" | "disadvantage";

export type GameSystemRollConfig = {
  supportsAdvantage: boolean;
  d20RollTypes: readonly SheetRollType[];
};

const DND5E_D20_ROLL_TYPES: readonly SheetRollType[] = [
  "ability_check",
  "saving_throw",
  "skill_check",
  "attack_roll",
  "initiative",
];

const SYSTEM_ROLL_CONFIG: Record<string, GameSystemRollConfig> = {
  dnd5e: {
    supportsAdvantage: true,
    d20RollTypes: DND5E_D20_ROLL_TYPES,
  },
  cyberpunk_red: {
    supportsAdvantage: false,
    d20RollTypes: [],
  },
  vtm_v5: {
    supportsAdvantage: false,
    d20RollTypes: [],
  },
};

const DEFAULT_CONFIG: GameSystemRollConfig = {
  supportsAdvantage: false,
  d20RollTypes: [],
};

export function getSystemRollConfig(systemId: string | undefined): GameSystemRollConfig {
  if (!systemId) return DEFAULT_CONFIG;
  return SYSTEM_ROLL_CONFIG[systemId] ?? DEFAULT_CONFIG;
}

export function supportsAdvantage(systemId: string | undefined): boolean {
  return getSystemRollConfig(systemId).supportsAdvantage;
}

export function isD20RollType(systemId: string | undefined, rollType: SheetRollType): boolean {
  return getSystemRollConfig(systemId).d20RollTypes.includes(rollType);
}

export function mergeAdvantageIntoContext(
  context: SheetRollContext | undefined,
  mode: AdvantageMode,
): SheetRollContext {
  const base = { ...(context ?? {}) };
  delete base.advantage;
  delete base.disadvantage;
  if (mode === "advantage") return { ...base, advantage: true };
  if (mode === "disadvantage") return { ...base, disadvantage: true };
  return base;
}

export type SceneDiceRollOptions = {
  expression: string;
  modifier?: number;
  advantage?: boolean;
  disadvantage?: boolean;
};

export function buildSceneDicePayload(
  systemId: string | undefined,
  expression: string,
  mode: AdvantageMode,
  modifier = 0,
): SceneDiceRollOptions {
  const payload: SceneDiceRollOptions = { expression, modifier };
  if (supportsAdvantage(systemId) && isSingleD20Expression(expression)) {
    if (mode === "advantage") payload.advantage = true;
    if (mode === "disadvantage") payload.disadvantage = true;
  }
  return payload;
}

export function isSingleD20Expression(expression: string): boolean {
  const normalized = expression.trim().toLowerCase().replace(/\s+/g, "");
  return /^1d20(?:[+-]\d+)?$/i.test(normalized);
}
