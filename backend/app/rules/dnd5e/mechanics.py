"""D&D 5e sheet calculations shared by plugin and tests."""

from typing import Any


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
