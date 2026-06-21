"""Map Open5e v2 creature stat blocks to backend Dnd5eSheet dicts."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from app.rules.dnd5e.damage_types import normalize_damage_type
from app.rules.dnd5e.schema import Dnd5eSheet, SKILL_ABILITY_MAP, skill_label_es

_ABILITY_SHORT = {
    "strength": "str",
    "dexterity": "dex",
    "constitution": "con",
    "intelligence": "int",
    "wisdom": "wis",
    "charisma": "cha",
}

_DIE_TYPE_PATTERN = re.compile(r"^D(\d+)$", re.IGNORECASE)
_DAMAGE_DESC_PATTERN = re.compile(
    r"\((\d+d\d+(?:\s*[+-]\s*\d+)?)\)\s+(\w+)\s+damage",
    re.IGNORECASE,
)
_CR_PROFICIENCY = (
    (0, 4, 2),
    (5, 8, 3),
    (9, 12, 4),
    (13, 16, 5),
    (17, 20, 6),
    (21, 24, 7),
    (25, 28, 8),
    (29, 32, 9),
)


def open5e_key_to_slug(key: str) -> str:
    trimmed = key.strip()
    if trimmed.startswith("srd_"):
        return trimmed[4:]
    return trimmed


def normalize_monster_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().lower())
    without_accents = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return re.sub(r"[\s_-]+", "", without_accents)


def proficiency_bonus_from_cr(challenge_rating: float) -> int:
    cr = max(0.0, float(challenge_rating))
    for low, high, bonus in _CR_PROFICIENCY:
        if low <= cr <= high:
            return bonus
    return 9


def _ability_modifiers(scores: dict[str, Any]) -> dict[str, int]:
    mods: dict[str, int] = {}
    for full, short in _ABILITY_SHORT.items():
        score = scores.get(full, 10)
        mods[short] = (int(score) - 10) // 2 if isinstance(score, int) else 0
    return mods


def _derive_saving_throws(
    creature: dict[str, Any],
    *,
    modifiers: dict[str, int],
    proficiency_bonus: int,
) -> list[str]:
    saving_throws = creature.get("saving_throws")
    if not isinstance(saving_throws, dict):
        return []

    proficient: list[str] = []
    for full, short in _ABILITY_SHORT.items():
        bonus = saving_throws.get(full)
        if not isinstance(bonus, int):
            continue
        base = modifiers.get(short, 0)
        if bonus - base >= proficiency_bonus:
            proficient.append(short)
    return proficient


def _derive_skills(
    creature: dict[str, Any],
    *,
    modifiers: dict[str, int],
    proficiency_bonus: int,
) -> list[dict[str, Any]]:
    skill_bonuses = creature.get("skill_bonuses")
    if not isinstance(skill_bonuses, dict):
        return []

    entries: list[dict[str, Any]] = []
    for skill_key, bonus in skill_bonuses.items():
        if not isinstance(skill_key, str) or not isinstance(bonus, int):
            continue
        ability = SKILL_ABILITY_MAP.get(skill_key.strip().lower().replace(" ", "_"))
        if ability is None:
            continue
        base = modifiers.get(ability, 0)
        diff = bonus - base
        if diff >= proficiency_bonus * 2:
            entries.append(
                {
                    "name": skill_label_es(skill_key),
                    "proficient": True,
                    "expertise": True,
                }
            )
        elif diff >= proficiency_bonus:
            entries.append(
                {
                    "name": skill_label_es(skill_key),
                    "proficient": True,
                    "expertise": False,
                }
            )
    return entries


def _parse_damage_from_desc(desc: str) -> tuple[str, str] | None:
    match = _DAMAGE_DESC_PATTERN.search(desc)
    if not match:
        return None
    dice = re.sub(r"\s+", "", match.group(1))
    damage_type = normalize_damage_type(match.group(2))
    return dice, damage_type


def _format_damage_dice(attack: dict[str, Any]) -> str:
    count = attack.get("damage_die_count")
    die_type = attack.get("damage_die_type", "D6")
    bonus = attack.get("damage_bonus")
    if isinstance(count, int) and count > 0:
        die_match = _DIE_TYPE_PATTERN.match(str(die_type))
        sides = die_match.group(1) if die_match else "6"
        dice = f"{count}d{sides}"
        if isinstance(bonus, int) and bonus != 0:
            dice += f"+{bonus}" if bonus > 0 else str(bonus)
        return dice
    return "1d4"


def _attack_damage_type(attack: dict[str, Any], desc: str) -> str:
    parsed = _parse_damage_from_desc(desc)
    if parsed:
        return parsed[1]
    damage_type = attack.get("damage_type")
    if isinstance(damage_type, dict):
        key = damage_type.get("key") or damage_type.get("name")
        if isinstance(key, str):
            return normalize_damage_type(key)
    return "contundente"


def _attack_damage_dice(attack: dict[str, Any], desc: str) -> str:
    parsed = _parse_damage_from_desc(desc)
    if parsed:
        return parsed[0]
    return _format_damage_dice(attack)


def _infer_attack_ability(attack: dict[str, Any], desc: str) -> str:
    lowered = desc.lower()
    if "ranged" in lowered or attack.get("range"):
        return "dex"
    return "str"


def _map_attacks(creature: dict[str, Any], *, proficiency_bonus: int) -> list[dict[str, Any]]:
    scores = creature.get("ability_scores") or {}
    if not isinstance(scores, dict):
        scores = {}
    abilities = {
        "str": int(scores.get("strength", 10)),
        "dex": int(scores.get("dexterity", 10)),
        "con": int(scores.get("constitution", 10)),
        "int": int(scores.get("intelligence", 10)),
        "wis": int(scores.get("wisdom", 10)),
        "cha": int(scores.get("charisma", 10)),
    }

    attacks: list[dict[str, Any]] = []
    actions = creature.get("actions")
    if not isinstance(actions, list):
        return attacks

    for action in actions:
        if not isinstance(action, dict):
            continue
        action_attacks = action.get("attacks")
        if not isinstance(action_attacks, list) or not action_attacks:
            continue
        desc = str(action.get("desc", ""))
        for attack in action_attacks:
            if not isinstance(attack, dict):
                continue
            to_hit = attack.get("to_hit_mod")
            if not isinstance(to_hit, int):
                continue
            ability = _infer_attack_ability(attack, desc)
            attacks.append(
                {
                    "name": str(action.get("name") or attack.get("name") or "Attack"),
                    "to_hit_bonus": to_hit,
                    "damage_dice": _attack_damage_dice(attack, desc),
                    "damage_type": _attack_damage_type(attack, desc),
                    "effect_type": "damage",
                    "ability": ability,
                    "proficient": True,
                }
            )
    return attacks


def _format_features(creature: dict[str, Any]) -> str:
    sections: list[str] = []
    traits = creature.get("traits")
    if isinstance(traits, list):
        for trait in traits:
            if isinstance(trait, dict):
                name = str(trait.get("name", "")).strip()
                desc = str(trait.get("desc", "")).strip()
                if name and desc:
                    sections.append(f"{name}. {desc}")
                elif desc:
                    sections.append(desc)

    actions = creature.get("actions")
    if isinstance(actions, list):
        for action in actions:
            if not isinstance(action, dict):
                continue
            action_attacks = action.get("attacks")
            if isinstance(action_attacks, list) and action_attacks:
                continue
            name = str(action.get("name", "")).strip()
            desc = str(action.get("desc", "")).strip()
            if name and desc:
                sections.append(f"{name}. {desc}")

    return "\n\n".join(sections)


def _damage_modifiers(creature: dict[str, Any]) -> dict[str, list[str]]:
    resistances_block = creature.get("resistances_and_immunities")
    if not isinstance(resistances_block, dict):
        return {"resistances": [], "vulnerabilities": [], "immunities": []}

    def _normalize_list(raw: object) -> list[str]:
        if not isinstance(raw, list):
            return []
        result: list[str] = []
        for item in raw:
            if isinstance(item, str) and item.strip():
                result.append(normalize_damage_type(item.strip()))
            elif isinstance(item, dict):
                key = item.get("key") or item.get("name")
                if isinstance(key, str):
                    result.append(normalize_damage_type(key))
        return result

    return {
        "resistances": _normalize_list(resistances_block.get("damage_resistances")),
        "vulnerabilities": _normalize_list(resistances_block.get("damage_vulnerabilities")),
        "immunities": _normalize_list(resistances_block.get("damage_immunities")),
    }


def format_challenge_rating_display(
    challenge_rating: float | int | str | None,
    *,
    raw: str | None = None,
) -> str:
    """Format CR for Spanish MM display (e.g. 0.25 → 1/4)."""
    if raw and raw.strip():
        return raw.strip().split("(", 1)[0].strip()
    if challenge_rating is None:
        return "?"
    if isinstance(challenge_rating, str):
        stripped = challenge_rating.strip()
        if "/" in stripped:
            return stripped.split("(", 1)[0].strip()
        try:
            challenge_rating = float(stripped)
        except ValueError:
            return stripped

    cr = float(challenge_rating)
    for num, den in ((1, 8), (1, 4), (1, 2), (3, 4), (5, 8)):
        if abs(cr - num / den) < 1e-6:
            return f"{num}/{den}"
    if cr == int(cr):
        return str(int(cr))
    return str(cr)


def build_creature_concept(creature: dict[str, Any]) -> str:
    """Build a useful identity concept without redundant name/CR noise."""
    explicit = str(creature.get("concept") or "").strip()
    if explicit:
        return explicit

    type_line = str(creature.get("type_line") or "").strip()
    if type_line:
        return type_line

    name = str(creature.get("name", "Monstruo"))
    creature_type = ""
    size = ""
    type_obj = creature.get("type")
    if isinstance(type_obj, dict):
        creature_type = str(type_obj.get("name", ""))
    size_obj = creature.get("size")
    if isinstance(size_obj, dict):
        size = str(size_obj.get("name", ""))

    alignment = str(creature.get("alignment", "")).strip()
    parts = [part for part in (creature_type, size) if part]
    concept = " ".join(parts)
    if alignment:
        concept = f"{concept}, {alignment}" if concept else alignment
    return concept or name


def build_narrative_template(creature: dict[str, Any]) -> dict[str, Any]:
    name = str(creature.get("name", "Monstruo"))

    traits: list[str] = []
    for trait in creature.get("traits") or []:
        if isinstance(trait, dict):
            trait_name = str(trait.get("name", "")).strip()
            if trait_name:
                traits.append(trait_name.lower())

    alignment = str(creature.get("alignment", "")).strip()
    if alignment and alignment not in traits:
        traits.append(alignment)

    public_description = str(creature.get("public_description") or "").strip()
    if not public_description:
        public_description = f"Un {name.lower()} del bestiario SRD."

    return {
        "concept": build_creature_concept(creature),
        "public_description": public_description,
        "personality_traits": traits or ["hostil"],
        "voice_and_tone": "Amenazante y directo",
        "secret_lore_master": "",
    }


class MonsterSheetMapper:
    """Open5e v2 creature → validated Dnd5eSheet dict."""

    @staticmethod
    def map_creature(creature: dict[str, Any]) -> dict[str, Any]:
        scores = creature.get("ability_scores") or {}
        if not isinstance(scores, dict):
            scores = {}

        cr = float(creature.get("challenge_rating") or 0)
        proficiency_bonus = creature.get("proficiency_bonus")
        if not isinstance(proficiency_bonus, int):
            proficiency_bonus = proficiency_bonus_from_cr(cr)

        modifiers = creature.get("modifiers")
        if not isinstance(modifiers, dict):
            modifiers = _ability_modifiers(scores)

        hp = int(creature.get("hit_points") or 10)
        initiative = creature.get("initiative_bonus")
        if not isinstance(initiative, int):
            initiative = modifiers.get("dex", 0)

        sheet = {
            "abilities": {
                "str": int(scores.get("strength", 10)),
                "dex": int(scores.get("dexterity", 10)),
                "con": int(scores.get("constitution", 10)),
                "int": int(scores.get("intelligence", 10)),
                "wis": int(scores.get("wisdom", 10)),
                "cha": int(scores.get("charisma", 10)),
            },
            "proficiency_bonus": proficiency_bonus,
            "skills": _derive_skills(creature, modifiers=modifiers, proficiency_bonus=proficiency_bonus),
            "saving_throws": _derive_saving_throws(
                creature,
                modifiers=modifiers,
                proficiency_bonus=proficiency_bonus,
            ),
            "ac": int(creature.get("armor_class") or 10),
            "hp": {"max": hp, "current": hp, "temp": 0},
            "hit_dice": str(creature.get("hit_dice") or ""),
            "death_saves": {"successes": 0, "failures": 0},
            "damage_modifiers": _damage_modifiers(creature),
            "initiative_modifier": initiative,
            "identity": {
                "class": "",
                "level": 1,
                "background": "",
                "race": str((creature.get("type") or {}).get("name", "") if isinstance(creature.get("type"), dict) else ""),
                "alignment": str(creature.get("alignment", "")),
            },
            "roleplay": {
                "personality_traits": "",
                "ideals": "",
                "bonds": "",
                "flaws": "",
                "inspiration": False,
            },
            "features_traits": _format_features(creature),
            "equipment": str(creature.get("armor_detail") or ""),
            "currency": {"cp": 0, "sp": 0, "ep": 0, "gp": 0, "pp": 0},
            "conditions": [],
            "attacks": _map_attacks(creature, proficiency_bonus=proficiency_bonus),
        }

        validated = Dnd5eSheet.model_validate(sheet)
        return validated.model_dump(mode="json")
