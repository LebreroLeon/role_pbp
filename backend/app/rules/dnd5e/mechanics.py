"""D&D 5e sheet calculations shared by plugin and tests."""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

from app.rules.dnd5e.damage_types import DND5E_DAMAGE_TYPE_SLUGS, normalize_damage_type


def ability_modifier(score: int) -> int:
    return (score - 10) // 2


def passive_perception(
    wis_score: int,
    proficiency_bonus: int,
    *,
    perception_proficient: bool = False,
    perception_expertise: bool = False,
) -> int:
    """Passive Wisdom (Perception) = 10 + WIS mod + proficiency if proficient."""
    mod = ability_modifier(wis_score)
    if perception_proficient:
        mod += proficiency_bonus
    if perception_expertise:
        mod += proficiency_bonus
    return 10 + mod


def _find_perception_flags(skills: list[Any]) -> tuple[bool, bool]:
    proficient = False
    expertise = False
    for entry in skills:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name", "")).strip().lower().replace(" ", "_")
        if name != "perception":
            continue
        proficient = bool(entry.get("proficient", False))
        expertise = bool(entry.get("expertise", False))
        break
    return proficient, expertise


def passive_perception_from_sheet(
    abilities: dict[str, Any],
    proficiency_bonus: int,
    skills: list[Any],
) -> int:
    wis_score = abilities.get("wis", 10)
    if not isinstance(wis_score, int):
        wis_score = 10
    proficient, expertise = _find_perception_flags(skills)
    return passive_perception(
        wis_score,
        proficiency_bonus,
        perception_proficient=proficient,
        perception_expertise=expertise,
    )


def apply_death_save_roll(
    natural: int,
    successes: int,
    failures: int,
    hp_current: int,
) -> dict[str, Any]:
    """Apply a death save d20 result per D&D 5e rules."""
    new_successes = successes
    new_failures = failures
    new_hp = hp_current
    outcome: str

    if natural == 20:
        new_hp = 1
        new_successes = 0
        new_failures = 0
        outcome = "critical_success"
    elif natural == 1:
        new_failures = min(3, failures + 2)
        outcome = "critical_failure"
    elif natural >= 10:
        new_successes = min(3, successes + 1)
        outcome = "success"
    else:
        new_failures = min(3, failures + 1)
        outcome = "failure"

    stabilized = new_successes >= 3
    dead = new_failures >= 3

    return {
        "natural": natural,
        "outcome": outcome,
        "successes": new_successes,
        "failures": new_failures,
        "hp_current": new_hp,
        "stabilized": stabilized,
        "dead": dead,
        "is_success": outcome in {"success", "critical_success"},
    }


def double_damage_dice(expression: str) -> str:
    """Double the dice count in a damage expression (D&D 5e critical hits)."""
    expr = expression.strip()
    match = re.match(r"^(\d+)d(\d+)(.*)$", expr, re.IGNORECASE)
    if not match:
        return expr
    count = int(match.group(1)) * 2
    return f"{count}d{match.group(2)}{match.group(3)}"


def _normalize_slug_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    result: list[str] = []
    for item in values:
        if isinstance(item, str) and item.strip():
            slug = normalize_damage_type(item.strip(), default="")
            if slug and slug in DND5E_DAMAGE_TYPE_SLUGS:
                result.append(slug)
    return result


def get_damage_modifiers(sheet: dict[str, Any]) -> dict[str, list[str]]:
    """Read resistances, vulnerabilities, and immunities from nested or flat sheets."""
    resistances: list[str] = []
    vulnerabilities: list[str] = []
    immunities: list[str] = []

    def apply_block(block: dict[str, Any]) -> None:
        nonlocal resistances, vulnerabilities, immunities
        parsed_resist = _normalize_slug_list(block.get("resistances"))
        parsed_vuln = _normalize_slug_list(block.get("vulnerabilities"))
        parsed_immune = _normalize_slug_list(block.get("immunities"))
        if parsed_resist:
            resistances = parsed_resist
        if parsed_vuln:
            vulnerabilities = parsed_vuln
        if parsed_immune:
            immunities = parsed_immune

    defense = sheet.get("defense")
    if isinstance(defense, dict):
        dmg_mod = defense.get("damage_modifiers")
        if isinstance(dmg_mod, dict):
            apply_block(dmg_mod)

    dmg_mod = sheet.get("damage_modifiers")
    if isinstance(dmg_mod, dict):
        apply_block(dmg_mod)

    return {
        "resistances": resistances,
        "vulnerabilities": vulnerabilities,
        "immunities": immunities,
    }


def apply_damage_modifiers(amount: int, damage_type: str, sheet: dict[str, Any]) -> tuple[int, str | None]:
    """Apply resistances, vulnerabilities, and immunities. Returns (final_amount, label)."""
    dtype = normalize_damage_type(damage_type)
    mods = get_damage_modifiers(sheet)
    if dtype in mods["immunities"]:
        return 0, "inmunidad"
    if dtype in mods["vulnerabilities"]:
        return amount * 2, "vulnerabilidad"
    if dtype in mods["resistances"]:
        return amount // 2, "resistencia"
    return amount, None


def _read_hp_block(sheet: dict[str, Any]) -> dict[str, int]:
    defense = sheet.get("defense")
    if isinstance(defense, dict) and isinstance(defense.get("hp"), dict):
        hp = defense["hp"]
        return {
            "max": int(hp.get("max", 0) or 0),
            "current": int(hp.get("current", 0) or 0),
            "temp": int(hp.get("temp", 0) or 0),
        }
    hp = sheet.get("hp")
    if isinstance(hp, dict):
        return {
            "max": int(hp.get("max", 0) or 0),
            "current": int(hp.get("current", 0) or 0),
            "temp": int(hp.get("temp", 0) or 0),
        }
    return {"max": 0, "current": 0, "temp": 0}


def _read_death_saves(sheet: dict[str, Any]) -> dict[str, int]:
    defense = sheet.get("defense")
    if isinstance(defense, dict) and isinstance(defense.get("death_saves"), dict):
        ds = defense["death_saves"]
        return {
            "successes": int(ds.get("successes", 0) or 0),
            "failures": int(ds.get("failures", 0) or 0),
        }
    ds = sheet.get("death_saves")
    if isinstance(ds, dict):
        return {
            "successes": int(ds.get("successes", 0) or 0),
            "failures": int(ds.get("failures", 0) or 0),
        }
    return {"successes": 0, "failures": 0}


def _write_hp_block(sheet: dict[str, Any], hp: dict[str, int]) -> None:
    if isinstance(sheet.get("defense"), dict):
        sheet["defense"]["hp"] = dict(hp)
    sheet["hp"] = dict(hp)


def _write_death_saves(sheet: dict[str, Any], death_saves: dict[str, int]) -> None:
    if isinstance(sheet.get("defense"), dict):
        sheet["defense"]["death_saves"] = dict(death_saves)
    sheet["death_saves"] = dict(death_saves)


def _format_damage_chat_summary(
    *,
    raw_amount: int,
    modified_amount: int,
    damage_type: str,
    modifier_label: str | None,
    hp_before: int,
    hp_after: int,
    is_instant_death: bool,
    death_save_failures_added: int,
) -> str:
    type_label = damage_type.replace("_", " ")
    if modifier_label and raw_amount != modified_amount:
        damage_line = f"{raw_amount} {type_label} → {modified_amount} ({modifier_label})"
    else:
        damage_line = f"{modified_amount} {type_label}"

    parts = [f"Daño {damage_line}: PV {hp_before} → {hp_after}"]
    if death_save_failures_added:
        parts.append(f"+{death_save_failures_added} fallo(s) de salvación")
    if is_instant_death:
        parts.append("muerte instantánea")
    return ". ".join(parts)


def apply_damage_pipeline(
    sheet_data: dict[str, Any],
    *,
    amount: int,
    damage_type: str,
    is_healing: bool = False,
    is_critical: bool = False,
) -> dict[str, Any]:
    """Single damage path for attacks and manual damage. Healing uses a separate branch."""
    if is_healing:
        raise ValueError("apply_damage_pipeline does not handle healing")

    updated = deepcopy(sheet_data)
    hp = _read_hp_block(updated)
    death_saves = _read_death_saves(updated)

    hp_before = hp["current"]
    hp_max = hp["max"]
    temp_before = hp["temp"]

    raw_amount = amount
    modified_amount, modifier_label = apply_damage_modifiers(amount, damage_type, updated)

    death_save_failures_added = 0
    is_instant_death = False
    is_dead = False

    if hp_before <= 0:
        death_save_failures_added = 2 if is_critical else 1
        death_saves["failures"] = min(3, death_saves["failures"] + death_save_failures_added)
        if death_saves["failures"] >= 3:
            is_dead = True
        hp_after = hp_before
        _write_death_saves(updated, death_saves)
    else:
        remaining = modified_amount
        if hp["temp"] > 0:
            absorbed = min(hp["temp"], remaining)
            hp["temp"] -= absorbed
            remaining -= absorbed

        hp_after = max(0, hp_before - remaining)
        hp["current"] = hp_after
        _write_hp_block(updated, hp)

        if hp_after == 0:
            overflow = max(0, remaining - hp_before)
            if overflow >= hp_max:
                is_instant_death = True
                is_dead = True

    chat_summary = _format_damage_chat_summary(
        raw_amount=raw_amount,
        modified_amount=modified_amount,
        damage_type=damage_type,
        modifier_label=modifier_label,
        hp_before=hp_before,
        hp_after=hp_after,
        is_instant_death=is_instant_death,
        death_save_failures_added=death_save_failures_added,
    )

    return {
        "updated_sheet": updated,
        "hp_before": hp_before,
        "hp_after": hp_after,
        "temp_hp_before": temp_before,
        "temp_hp_after": hp["temp"],
        "raw_amount": raw_amount,
        "modified_amount": modified_amount,
        "damage_modifier": modifier_label,
        "amount_applied": raw_amount,
        "is_unconscious": hp_after == 0 and not is_dead,
        "is_instant_death": is_instant_death,
        "is_dead": is_dead,
        "death_save_failures_added": death_save_failures_added,
        "is_critical": is_critical,
        "chat_summary": chat_summary,
    }
