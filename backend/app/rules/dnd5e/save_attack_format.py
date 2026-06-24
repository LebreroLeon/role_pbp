from __future__ import annotations

from app.rules.dnd5e.damage_types import (
    DND5E_DAMAGE_TYPE_SLUGS,
    PLACEHOLDER_DAMAGE_TYPES,
    normalize_damage_type,
    resolve_damage_type_slug,
)

DAMAGE_TYPE_LABELS_ES: dict[str, str] = {
    "contundente": "contundente",
    "cortante": "cortante",
    "perforante": "perforante",
    "acido": "ácido",
    "frio": "frío",
    "fuego": "fuego",
    "relampago": "relámpago",
    "trueno": "trueno",
    "veneno": "veneno",
    "fuerza": "fuerza",
    "necrotico": "necrótico",
    "psiquico": "psíquico",
    "radiante": "radiante",
}

def damage_type_label_es(damage_type: str | None) -> str | None:
    if not damage_type or not str(damage_type).strip():
        return None
    normalized = str(damage_type).strip().lower()
    if normalized in PLACEHOLDER_DAMAGE_TYPES:
        return None
    slug = resolve_damage_type_slug(damage_type)
    if slug is None or slug not in DND5E_DAMAGE_TYPE_SLUGS:
        return None
    return DAMAGE_TYPE_LABELS_ES.get(slug)


def format_save_attack_roll_line(
    *,
    defender_name: str,
    ability_label: str,
    total: int,
    save_dc: int,
    save_succeeded: bool,
    attacker_name: str,
    half_on_save: bool = False,
    applies_damage: bool = False,
) -> str:
    score = f"({total} vs CD {save_dc})"
    verb = "supera" if save_succeeded else "falla"
    line = f"{defender_name} {verb} la salvación de {ability_label} {score}"

    if save_succeeded:
        if applies_damage and half_on_save:
            line += f" — sufre la mitad del daño de {attacker_name}."
        else:
            line += f" — el hechizo de {attacker_name} no le afecta."
    elif applies_damage:
        line += " — sufre el efecto completo."
    else:
        line += f" — queda afectado por el hechizo de {attacker_name}."

    return line


def format_save_damage_taken_line(
    *,
    defender_name: str,
    amount: int,
    damage_type: str | None = None,
) -> str:
    type_label = damage_type_label_es(damage_type)
    if type_label:
        return f"{defender_name} pierde {amount} PV de {type_label}"
    return f"{defender_name} pierde {amount} PV"
