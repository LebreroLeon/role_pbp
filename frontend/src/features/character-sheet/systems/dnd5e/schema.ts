import { z } from "zod";

export const DND5E_ABILITIES = ["str", "dex", "con", "int", "wis", "cha"] as const;
export type Dnd5eAbility = (typeof DND5E_ABILITIES)[number];

export const DND5E_ABILITY_LABELS: Record<Dnd5eAbility, string> = {
  str: "Fuerza",
  dex: "Destreza",
  con: "Constitución",
  int: "Inteligencia",
  wis: "Sabiduría",
  cha: "Carisma",
};

export const DND5E_SKILLS = [
  "Acrobatics",
  "Animal Handling",
  "Arcana",
  "Athletics",
  "Deception",
  "History",
  "Insight",
  "Intimidation",
  "Investigation",
  "Medicine",
  "Nature",
  "Perception",
  "Performance",
  "Persuasion",
  "Religion",
  "Sleight of Hand",
  "Stealth",
  "Survival",
] as const;

const abilityScore = z.number().int().min(1).max(30);

const skillSchema = z.object({
  name: z.string(),
  proficient: z.boolean(),
  expertise: z.boolean(),
});

const attackSchema = z.object({
  name: z.string().min(1, "Nombre requerido"),
  ability: z.enum(DND5E_ABILITIES),
  proficient: z.boolean(),
  damage: z.object({
    dice: z.string().min(1, "Dados requeridos"),
    type: z.string().min(1, "Tipo requerido"),
  }),
  properties: z.array(z.string()),
});

export const dnd5eSheetSchema = z.object({
  abilities: z.object({
    str: abilityScore,
    dex: abilityScore,
    con: abilityScore,
    int: abilityScore,
    wis: abilityScore,
    cha: abilityScore,
  }),
  proficiency: z.object({
    bonus: z.number().int().min(0).max(10),
    saving_throws: z.array(z.enum(DND5E_ABILITIES)),
    skills: z.array(skillSchema),
  }),
  defense: z.object({
    ac: z.number().int().min(0).max(40),
    hp: z.object({
      max: z.number().int().min(1),
      current: z.number().int().min(0),
      temp: z.number().int().min(0),
    }),
    hit_dice: z.string(),
    death_saves: z.object({
      successes: z.number().int().min(0).max(3),
      failures: z.number().int().min(0).max(3),
    }),
  }),
  attacks: z.array(attackSchema).min(1),
  initiative: z.object({
    modifier: z.number().int(),
  }),
  conditions: z.array(z.string()),
});

export type Dnd5eSheet = z.infer<typeof dnd5eSheetSchema>;

export function abilityModifier(score: number): number {
  return Math.floor((score - 10) / 2);
}

export function defaultDnd5eSheet(): Dnd5eSheet {
  return {
    abilities: { str: 10, dex: 10, con: 10, int: 10, wis: 10, cha: 10 },
    proficiency: {
      bonus: 2,
      saving_throws: [],
      skills: DND5E_SKILLS.map((name) => ({ name, proficient: false, expertise: false })),
    },
    defense: {
      ac: 10,
      hp: { max: 10, current: 10, temp: 0 },
      hit_dice: "1d8",
      death_saves: { successes: 0, failures: 0 },
    },
    attacks: [
      {
        name: "Ataque desarmado",
        ability: "str",
        proficient: true,
        damage: { dice: "1d4", type: "contundente" },
        properties: [],
      },
    ],
    initiative: { modifier: 0 },
    conditions: [],
  };
}

export function parseDnd5eSheet(raw: unknown): Dnd5eSheet {
  const result = dnd5eSheetSchema.safeParse(raw);
  if (result.success) return result.data;
  return defaultDnd5eSheet();
}
