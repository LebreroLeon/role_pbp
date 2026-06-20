/**
 * Cyberpunk RED roll helpers — stub for future system-specific rolls.
 * Combat uses skill checks and d10 pools; no advantage/disadvantage.
 */

export type CyberpunkRollMode = "normal";

export function getCyberpunkRollMode(): CyberpunkRollMode {
  return "normal";
}

export function supportsCyberpunkAdvantage(): boolean {
  return false;
}
