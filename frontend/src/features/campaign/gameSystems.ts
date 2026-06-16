/**
 * Catálogo de sistemas de juego.
 *
 * Hoy `game_system` es solo metadata en campaña (etiqueta + futuro contexto IA).
 * No cambia dados, fichas ni reglas: eso llegará con perfiles por sistema.
 */
export type GameSystemCategory =
  | "d20"
  | "d100"
  | "dice_pool"
  | "narrative"
  | "other";

export type GameSystem = {
  value: string;
  label: string;
  category: GameSystemCategory;
};

export const GAME_SYSTEM_CATEGORIES: Record<GameSystemCategory, string> = {
  d20: "D20 / dado único + modificador",
  d100: "Percentil (d100)",
  dice_pool: "Pool de dados",
  narrative: "Narrativo / PbtA",
  other: "Otros",
};

export const GAME_SYSTEMS: GameSystem[] = [
  { value: "dnd5e", label: "D&D 5ª edición", category: "d20" },
  { value: "pathfinder2e", label: "Pathfinder 2e", category: "d20" },
  { value: "pathfinder1e", label: "Pathfinder 1e", category: "d20" },
  { value: "l5r_5e", label: "La leyenda de los Cinco Anillos (5ª ed.)", category: "dice_pool" },
  { value: "coc7", label: "La llamada de Cthulhu (7ª ed.)", category: "d100" },
  { value: "coc", label: "La llamada de Cthulhu (clásica)", category: "d100" },
  { value: "cyberpunk_red", label: "Cyberpunk RED", category: "dice_pool" },
  { value: "vtm_v5", label: "Vampiro: La Mascarada (5ª ed.)", category: "dice_pool" },
  { value: "werewolf5", label: "Hombre lobo: El Apocalipsis (5ª ed.)", category: "dice_pool" },
  { value: "mage_m20", label: "Mago: La Ascensión (M20)", category: "dice_pool" },
  { value: "savage_worlds", label: "Savage Worlds", category: "dice_pool" },
  { value: "warhammer_frb", label: "Warhammer Fantasía (4ª ed.)", category: "dice_pool" },
  { value: "blades", label: "Blades in the Dark", category: "dice_pool" },
  { value: "pbta", label: "Powered by the Apocalypse", category: "narrative" },
  { value: "fate", label: "Fate Core", category: "narrative" },
  { value: "generic", label: "Genérico / reglas de casa", category: "other" },
];

const CATEGORY_ORDER: GameSystemCategory[] = ["d20", "dice_pool", "d100", "narrative", "other"];

export const GAME_SYSTEM_GROUPS = CATEGORY_ORDER.map((category) => ({
  category,
  label: GAME_SYSTEM_CATEGORIES[category],
  systems: GAME_SYSTEMS.filter((system) => system.category === category),
})).filter((group) => group.systems.length > 0);

export function gameSystemLabel(value: string | null | undefined): string {
  if (!value) return "Sistema libre";
  return GAME_SYSTEMS.find((item) => item.value === value)?.label ?? value;
}
