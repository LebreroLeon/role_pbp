import { abilityModifier } from "./schema";

export function passivePerception(
  wisScore: number,
  proficiencyBonus: number,
  perceptionProficient: boolean,
  perceptionExpertise = false,
): number {
  let mod = abilityModifier(wisScore);
  if (perceptionProficient) mod += proficiencyBonus;
  if (perceptionExpertise) mod += proficiencyBonus;
  return 10 + mod;
}

export function applyDeathSaveRoll(
  natural: number,
  successes: number,
  failures: number,
  hpCurrent: number,
): {
  natural: number;
  outcome: string;
  successes: number;
  failures: number;
  hpCurrent: number;
  stabilized: boolean;
  dead: boolean;
  isSuccess: boolean;
} {
  let newSuccesses = successes;
  let newFailures = failures;
  let newHp = hpCurrent;
  let outcome: string;

  if (natural === 20) {
    newHp = 1;
    newSuccesses = 0;
    newFailures = 0;
    outcome = "critical_success";
  } else if (natural === 1) {
    newFailures = Math.min(3, failures + 2);
    outcome = "critical_failure";
  } else if (natural >= 10) {
    newSuccesses = Math.min(3, successes + 1);
    outcome = "success";
  } else {
    newFailures = Math.min(3, failures + 1);
    outcome = "failure";
  }

  return {
    natural,
    outcome,
    successes: newSuccesses,
    failures: newFailures,
    hpCurrent: newHp,
    stabilized: newSuccesses >= 3,
    dead: newFailures >= 3,
    isSuccess: outcome === "success" || outcome === "critical_success",
  };
}
