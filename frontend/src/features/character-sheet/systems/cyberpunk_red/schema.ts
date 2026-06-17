import { z } from "zod";

export const CYBERPUNK_STATS = [
  "int",
  "ref",
  "tech",
  "cool",
  "attr",
  "luck",
  "move",
  "body",
  "emp",
] as const;

export type CyberpunkStat = (typeof CYBERPUNK_STATS)[number];

export const CYBERPUNK_STAT_LABELS: Record<CyberpunkStat, string> = {
  int: "INT",
  ref: "REF",
  tech: "TECH",
  cool: "COOL",
  attr: "ATTR",
  luck: "LUCK",
  move: "MOVE",
  body: "BODY",
  emp: "EMP",
};

const statScore = z.number().int().min(1).max(10);

const skillSchema = z.object({
  name: z.string().min(1, "Nombre requerido"),
  stat: z.enum(CYBERPUNK_STATS),
  rank: z.number().int().min(0).max(10),
});

export const cyberpunkRedSheetSchema = z.object({
  stats: z.object({
    int: statScore,
    ref: statScore,
    tech: statScore,
    cool: statScore,
    attr: statScore,
    luck: statScore,
    move: statScore,
    body: statScore,
    emp: statScore,
  }),
  skills: z.array(skillSchema),
  hp: z.object({
    max: z.number().int().min(1),
    current: z.number().int().min(0),
  }),
  armor: z.object({
    head: z.number().int().min(0).max(25),
    body: z.number().int().min(0).max(25),
  }),
});

export type CyberpunkRedSheet = z.infer<typeof cyberpunkRedSheetSchema>;

export function defaultCyberpunkRedSheet(): CyberpunkRedSheet {
  return {
    stats: {
      int: 4,
      ref: 4,
      tech: 4,
      cool: 4,
      attr: 4,
      luck: 4,
      move: 4,
      body: 4,
      emp: 4,
    },
    skills: [],
    hp: { max: 40, current: 40 },
    armor: { head: 0, body: 0 },
  };
}

export function parseCyberpunkRedSheet(raw: unknown): CyberpunkRedSheet {
  const result = cyberpunkRedSheetSchema.safeParse(raw);
  if (result.success) return result.data;
  return defaultCyberpunkRedSheet();
}
