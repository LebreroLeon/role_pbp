export const GAME_SYSTEMS = [
  { value: "dnd5e", label: "D&D 5ª edición" },
  { value: "pathfinder2e", label: "Pathfinder 2e" },
  { value: "coc", label: "La llamada de Cthulhu" },
  { value: "pbta", label: "Powered by the Apocalypse" },
  { value: "generic", label: "Genérico / casa" },
] as const;

export function gameSystemLabel(value: string | null | undefined): string {
  if (!value) return "Sistema libre";
  return GAME_SYSTEMS.find((item) => item.value === value)?.label ?? value;
}
