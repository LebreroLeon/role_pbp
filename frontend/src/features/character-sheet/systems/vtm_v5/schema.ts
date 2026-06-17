import { z } from "zod";

export const VTM_PHYSICAL_ATTRS = ["str", "dex", "sta"] as const;
export const VTM_SOCIAL_ATTRS = ["cha", "man", "com"] as const;
export const VTM_MENTAL_ATTRS = ["int", "wil", "cer"] as const;

export const VTM_ATTRIBUTES = [
  ...VTM_PHYSICAL_ATTRS,
  ...VTM_SOCIAL_ATTRS,
  ...VTM_MENTAL_ATTRS,
] as const;

export type VtmAttribute = (typeof VTM_ATTRIBUTES)[number];

export const VTM_ATTRIBUTE_LABELS: Record<VtmAttribute, string> = {
  str: "Fuerza",
  dex: "Destreza",
  sta: "Vigor",
  cha: "Carisma",
  man: "Manipulación",
  com: "Compostura",
  int: "Inteligencia",
  wil: "Voluntad",
  cer: "Astucia",
};

export const VTM_SKILL_CATEGORIES = ["physical", "social", "mental"] as const;
export type VtmSkillCategory = (typeof VTM_SKILL_CATEGORIES)[number];

export const VTM_SKILL_CATEGORY_LABELS: Record<VtmSkillCategory, string> = {
  physical: "Física",
  social: "Social",
  mental: "Mental",
};

const attributeScore = z.number().int().min(1).max(5);

const skillSchema = z.object({
  name: z.string().min(1, "Nombre requerido"),
  category: z.enum(VTM_SKILL_CATEGORIES),
  dots: z.number().int().min(0).max(5),
});

const disciplineSchema = z.object({
  name: z.string().min(1, "Nombre requerido"),
  level: z.number().int().min(1).max(5),
});

export const vtmV5SheetSchema = z.object({
  attributes: z.object({
    str: attributeScore,
    dex: attributeScore,
    sta: attributeScore,
    cha: attributeScore,
    man: attributeScore,
    com: attributeScore,
    int: attributeScore,
    wil: attributeScore,
    cer: attributeScore,
  }),
  skills: z.array(skillSchema),
  disciplines: z.array(disciplineSchema),
  health: z.object({
    superficial: z.number().int().min(0),
    aggravated: z.number().int().min(0),
    max: z.number().int().min(1),
  }),
  hunger: z.number().int().min(0).max(5),
});

export type VtmV5Sheet = z.infer<typeof vtmV5SheetSchema>;

export function defaultVtmV5Sheet(): VtmV5Sheet {
  return {
    attributes: {
      str: 1,
      dex: 1,
      sta: 1,
      cha: 1,
      man: 1,
      com: 1,
      int: 1,
      wil: 1,
      cer: 1,
    },
    skills: [],
    disciplines: [],
    health: { superficial: 0, aggravated: 0, max: 7 },
    hunger: 1,
  };
}

export function parseVtmV5Sheet(raw: unknown): VtmV5Sheet {
  const result = vtmV5SheetSchema.safeParse(raw);
  if (result.success) return result.data;
  return defaultVtmV5Sheet();
}
