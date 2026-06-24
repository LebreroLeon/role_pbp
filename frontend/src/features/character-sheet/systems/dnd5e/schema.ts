import { z } from "zod";

import {
  DND5E_DAMAGE_TYPE_VALUES,
  normalizeDamageType,
  type Dnd5eDamageType,
} from "./damageTypes";

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
  resolution: z.enum(["attack_roll", "save"]),
  half_damage_on_save: z.boolean(),
  effect_type: z.enum(["damage", "healing"]),
  damage: z.object({
    dice: z.string().min(1, "Dados requeridos"),
    type: z.enum(DND5E_DAMAGE_TYPE_VALUES),
  }),
  properties: z.array(z.string()),
});

const levelSchema = z.number().int().min(1).max(20);

const spellSlotSchema = z.object({
  level: z.number().int().min(1).max(9),
  total: z.number().int().min(0),
  used: z.number().int().min(0),
});

const spellEntrySchema = z.object({
  name: z.string(),
  level: z.number().int().min(0).max(9),
  prepared: z.boolean(),
  ritual: z.boolean(),
  notes: z.string(),
});

const spellcastingSchema = z.object({
  ability: z.enum(DND5E_ABILITIES),
  save_dc: z.number().int().min(0).max(40).nullable(),
  attack_bonus: z.number().int().min(-10).max(30).nullable(),
  slots: z.array(spellSlotSchema),
  spells: z.array(spellEntrySchema),
});

export type Dnd5eSpellSlot = z.infer<typeof spellSlotSchema>;
export type Dnd5eSpellEntry = z.infer<typeof spellEntrySchema>;
export type Dnd5eSpellcasting = z.infer<typeof spellcastingSchema>;

const currencySchema = z.object({
  cp: z.number().int().min(0),
  sp: z.number().int().min(0),
  ep: z.number().int().min(0),
  gp: z.number().int().min(0),
  pp: z.number().int().min(0),
});

export const dnd5eSheetSchema = z.object({
  identity: z.object({
    class: z.string(),
    level: levelSchema,
    background: z.string(),
    race: z.string(),
    alignment: z.string(),
  }),
  roleplay: z.object({
    personality_traits: z.string(),
    ideals: z.string(),
    bonds: z.string(),
    flaws: z.string(),
    inspiration: z.boolean(),
  }),
  features_traits: z.string(),
  other_proficiencies: z.string(),
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
    speed: z.string(),
    death_saves: z.object({
      successes: z.number().int().min(0).max(3),
      failures: z.number().int().min(0).max(3),
    }),
    damage_modifiers: z.object({
      resistances: z.array(z.enum(DND5E_DAMAGE_TYPE_VALUES)),
      vulnerabilities: z.array(z.enum(DND5E_DAMAGE_TYPE_VALUES)),
      immunities: z.array(z.enum(DND5E_DAMAGE_TYPE_VALUES)),
    }),
  }),
  attacks: z.array(attackSchema).min(1),
  initiative: z.object({
    modifier: z.number().int(),
  }),
  conditions: z.array(z.string()),
  spellcasting: spellcastingSchema,
});

export type Dnd5eSheet = z.infer<typeof dnd5eSheetSchema>;

export function abilityModifier(score: number): number {
  return Math.floor((score - 10) / 2);
}

export const DND5E_SPELL_LEVEL_LABELS: Record<number, string> = {
  0: "Trucos",
  1: "Nivel 1",
  2: "Nivel 2",
  3: "Nivel 3",
  4: "Nivel 4",
  5: "Nivel 5",
  6: "Nivel 6",
  7: "Nivel 7",
  8: "Nivel 8",
  9: "Nivel 9",
};

export function defaultSpellSlots(): Dnd5eSpellSlot[] {
  return Array.from({ length: 9 }, (_, index) => ({
    level: index + 1,
    total: 0,
    used: 0,
  }));
}

export function defaultSpellcasting(): Dnd5eSpellcasting {
  return {
    ability: "int",
    save_dc: null,
    attack_bonus: null,
    slots: defaultSpellSlots(),
    spells: [],
  };
}

export function normalizeSpellSlots(raw: unknown): Dnd5eSpellSlot[] {
  const defaults = defaultSpellSlots();
  if (!Array.isArray(raw)) return defaults;
  const byLevel = new Map<number, Dnd5eSpellSlot>();
  for (const entry of raw) {
    if (!entry || typeof entry !== "object") continue;
    const level = (entry as { level?: number }).level;
    if (typeof level !== "number" || level < 1 || level > 9) continue;
    const total = (entry as { total?: number }).total;
    const used = (entry as { used?: number }).used;
    byLevel.set(level, {
      level,
      total: typeof total === "number" && total >= 0 ? Math.trunc(total) : 0,
      used: typeof used === "number" && used >= 0 ? Math.trunc(used) : 0,
    });
  }
  return defaults.map((slot) => byLevel.get(slot.level) ?? slot);
}

export function normalizeSpellEntries(raw: unknown): Dnd5eSpellEntry[] {
  if (!Array.isArray(raw)) return [];
  return raw
    .filter((entry): entry is Record<string, unknown> => Boolean(entry) && typeof entry === "object")
    .map((entry) => ({
      name: typeof entry.name === "string" ? entry.name : "",
      level:
        typeof entry.level === "number"
          ? Math.min(9, Math.max(0, Math.trunc(entry.level)))
          : 0,
      prepared: entry.prepared === true,
      ritual: entry.ritual === true,
      notes: typeof entry.notes === "string" ? entry.notes : "",
    }));
}

export function readSpellcasting(raw: unknown): Dnd5eSpellcasting {
  const defaults = defaultSpellcasting();
  if (!raw || typeof raw !== "object") return defaults;
  const entry = raw as Record<string, unknown>;
  const abilityRaw = typeof entry.ability === "string" ? entry.ability : defaults.ability;
  const ability = DND5E_ABILITIES.includes(abilityRaw as Dnd5eAbility)
    ? (abilityRaw as Dnd5eAbility)
    : defaults.ability;
  return {
    ability,
    save_dc: typeof entry.save_dc === "number" ? entry.save_dc : null,
    attack_bonus: typeof entry.attack_bonus === "number" ? entry.attack_bonus : null,
    slots: normalizeSpellSlots(entry.slots),
    spells: normalizeSpellEntries(entry.spells),
  };
}

export function computedSpellSaveDc(
  ability: Dnd5eAbility,
  proficiencyBonus: number,
  abilities: Dnd5eSheet["abilities"],
): number {
  return 8 + proficiencyBonus + abilityModifier(abilities[ability] ?? 10);
}

export function computedSpellAttackBonus(
  ability: Dnd5eAbility,
  proficiencyBonus: number,
  abilities: Dnd5eSheet["abilities"],
): number {
  return proficiencyBonus + abilityModifier(abilities[ability] ?? 10);
}

export function skillLabelEs(skillName: string): string {
  const key = skillName.trim().toLowerCase().replace(/\s+/g, "_");
  return DND5E_SKILL_LABELS_ES[key] ?? skillName;
}

export function parseClassLevel(combined: string): { class: string; level: number } {
  const trimmed = combined.trim();
  if (!trimmed) {
    return { class: "", level: 1 };
  }
  const match = /^(.+?)\s+(\d+)\s*$/.exec(trimmed);
  if (match) {
    const level = Math.min(20, Math.max(1, Number.parseInt(match[2], 10)));
    return { class: match[1].trim(), level };
  }
  return { class: trimmed, level: 1 };
}

export function defaultDnd5eSheet(): Dnd5eSheet {
  return {
    identity: {
      class: "",
      level: 1,
      background: "",
      race: "",
      alignment: "",
    },
    roleplay: {
      personality_traits: "",
      ideals: "",
      bonds: "",
      flaws: "",
      inspiration: false,
    },
    features_traits: "",
    other_proficiencies: "",
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
      speed: "9 m (30 pies)",
      death_saves: { successes: 0, failures: 0 },
      damage_modifiers: { resistances: [], vulnerabilities: [], immunities: [] },
    },
    attacks: [
      {
        name: "Ataque desarmado",
        ability: "str",
        proficient: true,
        resolution: "attack_roll",
        half_damage_on_save: false,
        effect_type: "damage",
        damage: { dice: "1d4", type: "contundente" },
        properties: [],
      },
    ],
    initiative: { modifier: 0 },
    conditions: [],
    spellcasting: defaultSpellcasting(),
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
    inspiration: typeof entry.inspiration === "boolean" ? entry.inspiration : defaults.inspiration,
  };
}

function readSheetIdentity(raw: unknown): Dnd5eSheet["identity"] {
  const defaults = defaultDnd5eSheet().identity;
  if (!raw || typeof raw !== "object") return defaults;
  const entry = raw as Record<string, unknown>;

  const classDirect = readString(entry.class, "");
  const levelDirect = typeof entry.level === "number" ? entry.level : undefined;

  if (classDirect || levelDirect !== undefined) {
    return {
      class: classDirect,
      level:
        levelDirect !== undefined
          ? Math.min(20, Math.max(1, Math.trunc(levelDirect)))
          : defaults.level,
      background: readString(entry.background, defaults.background),
      race: readString(entry.race, defaults.race),
      alignment: readString(entry.alignment, defaults.alignment),
    };
  }

  if (typeof entry.class_level === "string" && entry.class_level.trim()) {
    const parsed = parseClassLevel(entry.class_level);
    return {
      class: parsed.class,
      level: parsed.level,
      background: readString(entry.background, defaults.background),
      race: readString(entry.race, defaults.race),
      alignment: readString(entry.alignment, defaults.alignment),
    };
  }

  return {
    class: defaults.class,
    level: defaults.level,
    background: readString(entry.background, defaults.background),
    race: readString(entry.race, defaults.race),
    alignment: readString(entry.alignment, defaults.alignment),
  };
}

function normalizeAttackDamageType(raw: string | undefined): Dnd5eDamageType {
  return normalizeDamageType(raw);
}

export function normalizeAttackEntry(raw: unknown): Dnd5eSheet["attacks"][number] {
  const defaults = defaultDnd5eSheet().attacks[0];
  if (!raw || typeof raw !== "object") return defaults;
  const entry = raw as Record<string, unknown>;
  const damageRaw = entry.damage;
  const damage =
    damageRaw && typeof damageRaw === "object"
      ? (damageRaw as { dice?: string; type?: string })
      : undefined;
  const abilityRaw = typeof entry.ability === "string" ? entry.ability : defaults.ability;
  const ability = DND5E_ABILITIES.includes(abilityRaw as Dnd5eAbility)
    ? (abilityRaw as Dnd5eAbility)
    : defaults.ability;
  return {
    name: typeof entry.name === "string" ? entry.name : defaults.name,
    ability,
    proficient: entry.proficient === true,
    resolution: entry.resolution === "save" ? "save" : "attack_roll",
    half_damage_on_save: entry.half_damage_on_save === true,
    effect_type: entry.effect_type === "healing" ? "healing" : "damage",
    damage: {
      dice: damage?.dice?.trim() || defaults.damage.dice,
      type: normalizeAttackDamageType(damage?.type),
    },
    properties: Array.isArray(entry.properties)
      ? entry.properties.filter((item): item is string => typeof item === "string")
      : [],
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
  const damageModsRaw = (raw.damage_modifiers ??
    (raw.defense as { damage_modifiers?: Record<string, unknown> } | undefined)?.damage_modifiers) as
    | { resistances?: string[]; vulnerabilities?: string[]; immunities?: string[] }
    | undefined;
  const normalizeModList = (values?: string[]) =>
    (values ?? [])
      .map((item) => normalizeAttackDamageType(item))
      .filter((item): item is Dnd5eDamageType => DND5E_DAMAGE_TYPE_VALUES.includes(item as Dnd5eDamageType));
  const defense = {
    ac: typeof raw.ac === "number" ? raw.ac : defaults.defense.ac,
    hp: {
      max: hpRaw?.max ?? defaults.defense.hp.max,
      current: hpRaw?.current ?? defaults.defense.hp.current,
      temp: hpRaw?.temp ?? defaults.defense.hp.temp,
    },
    hit_dice: readString(raw.hit_dice, defaults.defense.hit_dice),
    speed: readString(raw.speed, defaults.defense.speed),
    death_saves: {
      successes: deathSavesRaw?.successes ?? defaults.defense.death_saves.successes,
      failures: deathSavesRaw?.failures ?? defaults.defense.death_saves.failures,
    },
    damage_modifiers: {
      resistances: normalizeModList(damageModsRaw?.resistances),
      vulnerabilities: normalizeModList(damageModsRaw?.vulnerabilities),
      immunities: normalizeModList(damageModsRaw?.immunities),
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
            effect_type?: "damage" | "healing";
            damage_dice?: string;
            damage_type?: string;
            properties?: string[];
          };
          const legacy = entry as {
            resolution?: "attack_roll" | "save";
            half_damage_on_save?: boolean;
            save_ability?: Dnd5eAbility;
          };
          return normalizeAttackEntry({
            ...entry,
            resolution: legacy.resolution,
            half_damage_on_save: legacy.half_damage_on_save,
            ability: legacy.save_ability ?? entry.ability,
          });
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
    other_proficiencies: readString(raw.other_proficiencies, defaults.other_proficiencies),
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
    spellcasting: readSpellcasting(raw.spellcasting),
  };
}

export function mergeDnd5eSheetDefaults(raw: unknown): Dnd5eSheet {
  const defaults = defaultDnd5eSheet();
  if (!raw || typeof raw !== "object") return defaults;
  const entry = raw as Record<string, unknown>;
  return {
    ...defaults,
    ...(entry as Partial<Dnd5eSheet>),
    identity: {
      ...defaults.identity,
      ...(typeof entry.identity === "object" && entry.identity ? (entry.identity as Dnd5eSheet["identity"]) : {}),
    },
    roleplay: {
      ...defaults.roleplay,
      ...(typeof entry.roleplay === "object" && entry.roleplay ? (entry.roleplay as Dnd5eSheet["roleplay"]) : {}),
    },
    abilities: {
      ...defaults.abilities,
      ...(typeof entry.abilities === "object" && entry.abilities ? (entry.abilities as Dnd5eSheet["abilities"]) : {}),
    },
    proficiency: {
      ...defaults.proficiency,
      ...(typeof entry.proficiency === "object" && entry.proficiency
        ? (entry.proficiency as Dnd5eSheet["proficiency"])
        : {}),
    },
    defense: {
      ...defaults.defense,
      ...(typeof entry.defense === "object" && entry.defense ? (entry.defense as Dnd5eSheet["defense"]) : {}),
      hp: {
        ...defaults.defense.hp,
        ...(typeof entry.defense === "object" &&
        entry.defense &&
        typeof (entry.defense as Dnd5eSheet["defense"]).hp === "object"
          ? (entry.defense as Dnd5eSheet["defense"]).hp
          : {}),
      },
      death_saves: {
        ...defaults.defense.death_saves,
        ...(typeof entry.defense === "object" &&
        entry.defense &&
        typeof (entry.defense as Dnd5eSheet["defense"]).death_saves === "object"
          ? (entry.defense as Dnd5eSheet["defense"]).death_saves
          : {}),
      },
      damage_modifiers: {
        ...defaults.defense.damage_modifiers,
        ...(typeof entry.defense === "object" &&
        entry.defense &&
        typeof (entry.defense as Dnd5eSheet["defense"]).damage_modifiers === "object"
          ? (entry.defense as Dnd5eSheet["defense"]).damage_modifiers
          : {}),
      },
    },
    currency: {
      ...defaults.currency,
      ...(typeof entry.currency === "object" && entry.currency ? (entry.currency as Dnd5eSheet["currency"]) : {}),
    },
    initiative: {
      ...defaults.initiative,
      ...(typeof entry.initiative === "object" && entry.initiative
        ? (entry.initiative as Dnd5eSheet["initiative"])
        : {}),
    },
    features_traits: readString(entry.features_traits, defaults.features_traits),
    other_proficiencies: readString(entry.other_proficiencies, defaults.other_proficiencies),
    equipment: readString(entry.equipment, defaults.equipment),
    attacks: Array.isArray(entry.attacks) && entry.attacks.length > 0
      ? entry.attacks.map((attack) => normalizeAttackEntry(attack))
      : defaults.attacks,
    conditions: Array.isArray(entry.conditions)
      ? entry.conditions.filter((item): item is string => typeof item === "string")
      : defaults.conditions,
    spellcasting: readSpellcasting(entry.spellcasting),
  };
}

export function parseDnd5eSheet(raw: unknown): Dnd5eSheet {
  const merged = mergeDnd5eSheetDefaults(raw);
  const result = dnd5eSheetSchema.safeParse(merged);
  if (result.success) return result.data;

  if (isBackendFlatSheet(raw)) {
    const converted = convertBackendDnd5eSheet(raw);
    const revalidated = dnd5eSheetSchema.safeParse(converted);
    if (revalidated.success) return revalidated.data;
  }

  return defaultDnd5eSheet();
}
