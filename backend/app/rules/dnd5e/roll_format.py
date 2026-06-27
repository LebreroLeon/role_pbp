from __future__ import annotations

from app.rules.dnd5e.save_attack_format import damage_type_label_es

CRITICAL_MARKER = "¡CRÍTICO!"


def format_modifier_suffix(modifier: int) -> str:
    if modifier > 0:
        return f"+{modifier}"
    if modifier < 0:
        return str(modifier)
    return ""


def format_natural_plus_modifier(natural: int, modifier: int) -> str:
    if modifier:
        return f"{natural}{modifier:+d}"
    return str(natural)


def format_dice_rolls_sum(rolls: list[int]) -> str:
    if not rolls:
        return "?"
    return "+".join(str(value) for value in rolls)


def format_attack_roll_line(
    *,
    natural: int,
    modifier: int,
    total: int,
    dice_label: str = "1d20",
    target_ac: int | None = None,
    hit: bool | None = None,
    is_critical: bool = False,
    prefix: str = "Ataque: ",
) -> str:
    mod_suffix = format_modifier_suffix(modifier)
    expression = f"{dice_label}{mod_suffix}"
    breakdown = format_natural_plus_modifier(natural, modifier)
    line = f"{prefix}{expression} = {breakdown} = {total}"
    if target_ac is not None:
        line += f" vs CA {target_ac}"
        if hit is not None:
            line += f" — {'Impacto' if hit else 'Fallo'}"
    if is_critical:
        line += f" — {CRITICAL_MARKER}"
    return line


def format_damage_roll_line(
    *,
    expression: str,
    rolls: list[int],
    modifier: int,
    total: int,
    damage_type: str | None = None,
    is_healing: bool = False,
    is_critical: bool = False,
) -> str:
    label = "Curación" if is_healing else "Daño"
    rolls_part = format_dice_rolls_sum(rolls)
    if modifier:
        breakdown = f"{rolls_part}{modifier:+d}" if rolls_part != "?" else f"{modifier:+d}"
    else:
        breakdown = rolls_part
    line = f"{label}: {expression} = {breakdown} = {total}"
    type_label = damage_type_label_es(damage_type)
    if type_label:
        line += f" {type_label}"
    if is_critical:
        line += f" — {CRITICAL_MARKER}"
    return line
