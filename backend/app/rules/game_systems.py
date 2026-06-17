from dataclasses import dataclass
from typing import Literal

DiceMode = Literal["d20", "dice_pool", "d100", "generic"]


@dataclass(frozen=True)
class GameSystemProfile:
    system_id: str
    label: str
    dice_mode: DiceMode
    sheet_schema_version: str
    supported_roll_types: tuple[str, ...]
    combat_enabled: bool
    sheet_template_id: str


GAME_SYSTEM_PROFILES: dict[str, GameSystemProfile] = {
    "dnd5e": GameSystemProfile(
        system_id="dnd5e",
        label="D&D 5ª edición",
        dice_mode="d20",
        sheet_schema_version="1.0.0",
        supported_roll_types=(
            "ability_check",
            "saving_throw",
            "skill_check",
            "attack_roll",
            "damage",
            "initiative",
        ),
        combat_enabled=True,
        sheet_template_id="entity_pc_dnd5e_sheet",
    ),
    "cyberpunk_red": GameSystemProfile(
        system_id="cyberpunk_red",
        label="Cyberpunk RED",
        dice_mode="dice_pool",
        sheet_schema_version="0.1.0",
        supported_roll_types=(),
        combat_enabled=False,
        sheet_template_id="entity_pc_cyberpunk_red_sheet",
    ),
    "vtm_v5": GameSystemProfile(
        system_id="vtm_v5",
        label="Vampiro: La Mascarada (5ª ed.)",
        dice_mode="dice_pool",
        sheet_schema_version="0.1.0",
        supported_roll_types=(),
        combat_enabled=False,
        sheet_template_id="entity_pc_vtm_v5_sheet",
    ),
}


def get_profile(game_system: str | None) -> GameSystemProfile | None:
    if not game_system:
        return None
    return GAME_SYSTEM_PROFILES.get(game_system)
