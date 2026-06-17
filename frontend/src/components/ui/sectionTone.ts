export type SectionTone = "rose" | "violet" | "teal" | "amber" | "sky";

export const DEFAULT_SECTION_TONE: SectionTone = "violet";

/** Tono visual por ruta de campaña — una sola fuente de verdad. */
export function getToneFromPath(path: string): SectionTone {
  if (path.includes("/chat")) return "rose";
  if (path.includes("/fichas")) return "sky";
  if (path.includes("/ficha")) return "sky";
  if (path.includes("/biblioteca")) return "amber";
  if (path.includes("/mesa") || path.includes("/master")) return "teal";
  if (path.includes("/mundo") || path.includes("/entities")) return "violet";
  return DEFAULT_SECTION_TONE;
}
