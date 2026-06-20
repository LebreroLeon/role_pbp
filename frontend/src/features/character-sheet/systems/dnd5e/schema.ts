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

/** Skills ordered like the official D&D 5e character sheet (grouped by ability). */
export const DND5E_SKILL_GROUPS: ReadonlyArray<{
  ability: Dnd5eAbility;
  skills: readonly string[];
}> = [
  { ability: "str", skills: ["Athletics"] },
  { ability: "dex", skills: ["Acrobatics", "Sleight of Hand", "Stealth"] },
  { ability: "con", skills: [] },
  { ability: "int", skills: ["Arcana", "History", "Investigation", "Nature", "Religion"] },
  { ability: "wis", skills: ["Animal Handling", "Insight", "Medicine", "Perception", "Survival"] },
  { ability: "cha", skills: ["Deception", "Intimidation", "Performance", "Persuasion"] },
];

export const DND5E_SKILLS = DND5E_SKILL_GROUPS.flatMap((group) => group.skills);

export const DND5E_SKILL_LABELS_ES: Record<string, string> = {
  athletics: "Atletismo",
  acrobatics: "Acrobacias",
  sleight_of_hand: "Juego de manos",
  stealth: "Sigilo",
  arcana: "Arcano",
  history: "Historia",
  investigation: "Investigación",
  nature: "Naturaleza",
  religion: "Religión",
  animal_handling: "Trato con animales",
  insight: "Perspicacia",
  medicine: "Medicina",
  perception: "Percepción",
  survival: "Supervivencia",
  deception: "Engaño",
  intimidation: "Intimidación",
  performance: "Interpretación",
  persuasion: "Persuasión",
};

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

const currencySchema = z.object({
  cp: z.number().int().min(0),
  sp: z.number().int().min(0),
  ep: z.number().int().min(0),
  gp: z.number().int().min(0),
  pp: z.number().int().min(0),
});

export const dnd5eSheetSchema = z.object({
  identity: z.object({
    class_level: z.string(),
    background: z.string(),
    race: z.string(),
    alignment: z.string(),
  }),
  roleplay: z.object({
    personality_traits: z.string(),
    ideals: z.string(),
    bonds: z.string(),
    flaws: z.string(),
  }),
  features_traits: z.string(),
  equipment: z.string(),
  currency: currencySchema,
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

export function skillLabelEs(skillName: string): string {
  const key = skillName.trim().toLowerCase().replace(/\s+/g, "_");
  return DND5E_SKILL_LABELS_ES[key] ?? skillName;
}

export function defaultDnd5eSheet(): Dnd5eSheet {
  return {
    identity: {
      class_level: "",
      background: "",
      race: "",
      alignment: "",
    },
    roleplay: {
      personality_traits: "",
      ideals: "",
      bonds: "",
      flaws: "",
    },
    features_traits: "",
    equipment: "",
    currency: { cp: 0, sp: 0, ep: 0, gp: 0, pp: 0 },
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

function readString(raw: unknown, fallback = ""): string {
  return typeof raw === "string" ? raw : fallback;
}

function readCurrency(raw: unknown): Dnd5eSheet["currency"] {
  const defaults = defaultDnd5eSheet().currency;
  if (!raw || typeof raw !== "object") return defaults;
  const entry = raw as Record<string, unknown>;
  return {
    cp: typeof entry.cp === "number" ? entry.cp : defaults.cp,
    sp: typeof entry.sp === "number" ? entry.sp : defaults.sp,
    ep: typeof entry.ep === "number" ? entry.ep : defaults.ep,
    gp: typeof entry.gp === "number" ? entry.gp : defaults.gp,
    pp: typeof entry.pp === "number" ? entry.pp : defaults.pp,
  };
}

function readRoleplay(raw: unknown): Dnd5eSheet["roleplay"] {
  const defaults = defaultDnd5eSheet().roleplay;
  if (!raw || typeof raw !== "object") return defaults;
  const entry = raw as Record<string, unknown>;
  return {
    personality_traits: readString(entry.personality_traits, defaults.personality_traits),
    ideals: readString(entry.ideals, defaults.ideals),
    bonds: readString(entry.bonds, defaults.bonds),
    flaws: readString(entry.flaws, defaults.flaws),
  };
}

function readSheetIdentity(raw: unknown): Dnd5eSheet["identity"] {
  const defaults = defaultDnd5eSheet().identity;
  if (!raw || typeof raw !== "object") return defaults;
  const entry = raw as Record<string, unknown>;
  return {
    class_level: readString(entry.class_level, defaults.class_level),
    background: readString(entry.background, defaults.background),
    race: readString(entry.race, defaults.race),
    alignment: readString(entry.alignment, defaults.alignment),
  };
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
  const deathSavesRaw = raw.death_saves as { successes?: number; failures?: number } | undefined;
  const defense = {
    ac: typeof raw.ac === "number" ? raw.ac : defaults.defense.ac,
    hp: {
      max: hpRaw?.max ?? defaults.defense.hp.max,
      current: hpRaw?.current ?? defaults.defense.hp.current,
      temp: hpRaw?.temp ?? defaults.defense.hp.temp,
    },
    hit_dice: readString(raw.hit_dice, defaults.defense.hit_dice),
    death_saves: {
      successes: deathSavesRaw?.successes ?? defaults.defense.death_saves.successes,
      failures: deathSavesRaw?.failures ?? defaults.defense.death_saves.failures,
    },
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

  const initiativeModifier =
    typeof raw.initiative_modifier === "number"
      ? raw.initiative_modifier
      : defaults.initiative.modifier;

  return {
    identity: readSheetIdentity(raw.identity),
    roleplay: readRoleplay(raw.roleplay),
    features_traits: readString(raw.features_traits, defaults.features_traits),
    equipment: readString(raw.equipment, defaults.equipment),
    currency: readCurrency(raw.currency),
    abilities,
    proficiency: {
      bonus: proficiencyBonus,
      saving_throws,
      skills,
    },
    defense,
    attacks,
    initiative: { modifier: initiativeModifier },
    conditions: Array.isArray(raw.conditions)
      ? raw.conditions.filter((item): item is string => typeof item === "string")
      : defaults.conditions,
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
