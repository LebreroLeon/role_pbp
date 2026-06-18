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

function normalizeSkillKey(name: string): string {
  return name.trim().toLowerCase().replace(/\s+/g, "_");
}

function isBackendFlatSheet(raw: unknown): raw is Record<string, unknown> {
  if (!raw || typeof raw !== "object") return false;
  const sheet = raw as Record<string, unknown>;
  return !("proficiency" in sheet) && !("defense" in sheet) && ("ac" in sheet || "proficiency_bonus" in sheet);
}

/** Map backend canonical sheet (flat) to frontend nested editor shape. */
export function convertBackendDnd5eSheet(raw: Record<string, unknown>): Dnd5eSheet {
  const defaults = defaultDnd5eSheet();
  const abilitiesRaw = raw.abilities as Record<string, number> | undefined;

  const abilities = {
    str: abilitiesRaw?.str ?? defaults.abilities.str,
    dex: abilitiesRaw?.dex ?? defaults.abilities.dex,
    con: abilitiesRaw?.con ?? defaults.abilities.con,
    int: abilitiesRaw?.int ?? abilitiesRaw?.intelligence ?? defaults.abilities.int,
    wis: abilitiesRaw?.wis ?? defaults.abilities.wis,
    cha: abilitiesRaw?.cha ?? defaults.abilities.cha,
  };

  const proficiencyBonus =
    typeof raw.proficiency_bonus === "number" ? raw.proficiency_bonus : defaults.proficiency.bonus;

  const savingThrowsRaw = Array.isArray(raw.saving_throws) ? raw.saving_throws : [];
  const saving_throws = savingThrowsRaw.filter(
    (ability): ability is Dnd5eAbility =>
      typeof ability === "string" && DND5E_ABILITIES.includes(ability as Dnd5eAbility),
  );

  const skillsRaw = Array.isArray(raw.skills)
    ? (raw.skills as Array<{ name?: string; proficient?: boolean; expertise?: boolean }>)
    : [];
  const skillByKey = new Map(
    skillsRaw
      .filter((entry) => typeof entry.name === "string")
      .map((entry) => [normalizeSkillKey(entry.name!), entry] as const),
  );

  const skills = DND5E_SKILLS.map((name) => {
    const found = skillByKey.get(normalizeSkillKey(name));
    return {
      name,
      proficient: found?.proficient ?? false,
      expertise: found?.expertise ?? false,
    };
  });

  const hpRaw = raw.hp as { max?: number; current?: number; temp?: number } | undefined;
  const defense = {
    ac: typeof raw.ac === "number" ? raw.ac : defaults.defense.ac,
    hp: {
      max: hpRaw?.max ?? defaults.defense.hp.max,
      current: hpRaw?.current ?? defaults.defense.hp.current,
      temp: hpRaw?.temp ?? defaults.defense.hp.temp,
    },
    hit_dice: defaults.defense.hit_dice,
    death_saves: defaults.defense.death_saves,
  };

  const attacksRaw = Array.isArray(raw.attacks) ? raw.attacks : [];
  const attacks =
    attacksRaw.length > 0
      ? attacksRaw.map((attack) => {
          if (attack && typeof attack === "object" && "damage" in attack) {
            const parsed = attackSchema.safeParse(attack);
            if (parsed.success) return parsed.data;
          }
          const entry = attack as {
            name?: string;
            ability?: Dnd5eAbility;
            proficient?: boolean;
            damage_dice?: string;
            damage_type?: string;
            properties?: string[];
          };
          return {
            name: entry.name?.trim() || "Ataque",
            ability: entry.ability ?? "str",
            proficient: entry.proficient ?? false,
            damage: {
              dice: entry.damage_dice?.trim() || "1d4",
              type: entry.damage_type?.trim() || "contundente",
            },
            properties: entry.properties ?? [],
          };
        })
      : defaults.attacks;

  return {
    abilities,
    proficiency: {
      bonus: proficiencyBonus,
      saving_throws,
      skills,
    },
    defense,
    attacks,
    initiative: defaults.initiative,
    conditions: defaults.conditions,
  };
}

export function parseDnd5eSheet(raw: unknown): Dnd5eSheet {
  const result = dnd5eSheetSchema.safeParse(raw);
  if (result.success) return result.data;

  if (isBackendFlatSheet(raw)) {
    const converted = convertBackendDnd5eSheet(raw);
    const revalidated = dnd5eSheetSchema.safeParse(converted);
    if (revalidated.success) return revalidated.data;
  }

  return defaultDnd5eSheet();
}
