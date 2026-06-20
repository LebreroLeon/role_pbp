export const DND5E_DAMAGE_TYPE_GROUPS = [
  {
    label: "Físico",
    options: [
      { value: "contundente", label: "Contundente" },
      { value: "cortante", label: "Cortante" },
      { value: "perforante", label: "Perforante" },
    ],
  },
  {
    label: "Elemental / mágico",
    options: [
      { value: "acido", label: "Ácido" },
      { value: "frio", label: "Frío" },
      { value: "fuego", label: "Fuego" },
      { value: "relampago", label: "Relámpago" },
      { value: "trueno", label: "Trueno" },
      { value: "veneno", label: "Veneno" },
    ],
  },
  {
    label: "Místico / especial",
    options: [
      { value: "fuerza", label: "Fuerza" },
      { value: "necrotico", label: "Necrótico" },
      { value: "psiquico", label: "Psíquico" },
      { value: "radiante", label: "Radiante" },
    ],
  },
] as const;

export const DND5E_DAMAGE_TYPE_VALUES = [
  "contundente",
  "cortante",
  "perforante",
  "acido",
  "frio",
  "fuego",
  "relampago",
  "trueno",
  "veneno",
  "fuerza",
  "necrotico",
  "psiquico",
  "radiante",
] as const;

export type Dnd5eDamageType = (typeof DND5E_DAMAGE_TYPE_VALUES)[number];

const DAMAGE_TYPE_ALIASES: Record<string, Dnd5eDamageType> = {
  bludgeoning: "contundente",
  slashing: "cortante",
  piercing: "perforante",
  acid: "acido",
  cold: "frio",
  fire: "fuego",
  lightning: "relampago",
  thunder: "trueno",
  poison: "veneno",
  force: "fuerza",
  necrotic: "necrotico",
  psychic: "psiquico",
  radiant: "radiante",
  contundente: "contundente",
  cortante: "cortante",
  perforante: "perforante",
  acido: "acido",
  ácido: "acido",
  frio: "frio",
  frío: "frio",
  fuego: "fuego",
  relampago: "relampago",
  relámpago: "relampago",
  trueno: "trueno",
  veneno: "veneno",
  fuerza: "fuerza",
  necrotico: "necrotico",
  necrótico: "necrotico",
  psiquico: "psiquico",
  psíquico: "psiquico",
  radiante: "radiante",
};

function slugify(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[\s_-]+/g, "");
}

export function normalizeDamageType(raw: string | undefined, fallback: Dnd5eDamageType = "contundente"): Dnd5eDamageType {
  if (!raw?.trim()) return fallback;
  const key = slugify(raw);
  const mapped = DAMAGE_TYPE_ALIASES[key];
  if (mapped) return mapped;
  if ((DND5E_DAMAGE_TYPE_VALUES as readonly string[]).includes(key)) {
    return key as Dnd5eDamageType;
  }
  return fallback;
}

export function damageTypeLabel(value: string): string {
  for (const group of DND5E_DAMAGE_TYPE_GROUPS) {
    const match = group.options.find((option) => option.value === value);
    if (match) return match.label;
  }
  return value;
}
