/** D&D 5e roll helpers — re-exported from the systems registry for convenience. */

export {
  buildSceneDicePayload,
  isSingleD20Expression,
  mergeAdvantageIntoContext,
  supportsAdvantage,
  isD20RollType,
  type AdvantageMode,
} from "../registry";

export const DND5E_D20_ROLL_TYPES = [
  "ability_check",
  "saving_throw",
  "skill_check",
  "attack_roll",
  "initiative",
] as const;

export const SKILL_ABILITY_MAP: Record<string, string> = {
  acrobatics: "dex",
  animal_handling: "wis",
  arcana: "int",
  athletics: "str",
  deception: "cha",
  history: "int",
  insight: "wis",
  intimidation: "cha",
  investigation: "int",
  medicine: "wis",
  nature: "int",
  perception: "wis",
  performance: "cha",
  persuasion: "cha",
  religion: "int",
  sleight_of_hand: "dex",
  stealth: "dex",
  survival: "wis",
};

export function dnd5eSkillModifier(
  sheet: {
    abilities: Record<string, number>;
    proficiency: { bonus: number; skills: Array<{ name: string; proficient: boolean; expertise: boolean }> };
  },
  skillName: string,
  abilityModFn: (score: number) => number,
): number {
  const key = skillName.trim().toLowerCase().replace(/\s+/g, "_");
  const ability = SKILL_ABILITY_MAP[key] ?? "wis";
  const abilityScore = sheet.abilities[ability] ?? 10;
  let mod = abilityModFn(abilityScore);
  const skill = sheet.proficiency.skills.find(
    (entry) => entry.name.trim().toLowerCase().replace(/\s+/g, "_") === key,
  );
  if (skill?.proficient) mod += sheet.proficiency.bonus;
  if (skill?.expertise) mod += sheet.proficiency.bonus;
  return mod;
}
