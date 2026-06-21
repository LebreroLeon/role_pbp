"""Parse Spanish D&D 5e stat blocks from Edge manual PDF text."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any

from app.rules.dnd5e.damage_types import normalize_damage_type
from app.rules.dnd5e.monster_sheet_mapper import (
    MonsterSheetMapper,
    build_narrative_template,
    normalize_monster_name,
)
from app.rules.dnd5e.schema import Dnd5eSheet

_ABILITY_FULL = ("strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma")
_ABILITY_ES = ("FUE", "DES", "CON", "INT", "SAB", "CAR")
_SKILL_KEY_MAP = {
    "sigilo": "stealth",
    "atletismo": "athletics",
    "acrobacias": "acrobatics",
    "percepcion": "perception",
    "perspicacia": "insight",
    "investigacion": "investigation",
    "engano": "deception",
    "intimidacion": "intimidation",
    "persuasion": "persuasion",
    "historia": "history",
    "arcano": "arcana",
    "naturaleza": "nature",
    "religion": "religion",
    "medicina": "medicine",
    "supervivencia": "survival",
}

_TYPE_LINE = re.compile(
    r"^(?P<creature_type>\w+)\s+(?P<size>\w+)\s*\([^)]+\),\s*(?P<alignment>.+)$",
    re.MULTILINE | re.IGNORECASE,
)
_AC = re.compile(r"Clase de Armadura:\s*(\d+)(?:\s*\(([^)]+)\))?", re.IGNORECASE)
_HP = re.compile(r"Puntos de golpe:\s*(\d+)\s*\(([^)]+)\)", re.IGNORECASE)
_SPEED = re.compile(r"Velocidad:\s*(\d+)", re.IGNORECASE)
_CR = re.compile(r"Desaf[ií]o:\s*([\d/]+)", re.IGNORECASE)
_SKILLS = re.compile(r"Habilidades:\s*(.+)", re.IGNORECASE)
_ABILITY_SCORES = re.compile(
    r"(\d+)\s*\(([+-]?\d+)\)\s+"
    r"(\d+)\s*\(([+-]?\d+)\)\s+"
    r"(\d+)\s*\(([+-]?\d+)\)\s+"
    r"(\d+)\s*\(([+-]?\d+)\)\s+"
    r"(\d+)\s*\(([+-]?\d+)\)\s+"
    r"(\d+)\s*\(([+-]?\d+)\)",
)
_ATTACK = re.compile(
    r"(?P<name>[^.\n]+)\.\s*Ataque.*?:\s*\+(?P<to_hit>\d+)\s+a\s+impactar.*?Impacto:\s*\d+\s*\((?P<dice>[^)]+)\)\s*de\s+da[ñn]o\s+(?P<damage_type>\w+)",
    re.IGNORECASE | re.DOTALL,
)
_SECTION_HEADERS = re.compile(r"^(ACCIONES|REACCIONES|ACCIONES LEGENDARIAS)\s*$", re.MULTILINE | re.IGNORECASE)


def _normalize_text(value: str) -> str:
    return unicodedata.normalize("NFKC", value)


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().lower())
    without_accents = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return re.sub(r"[\s_-]+", "", without_accents)


def _parse_cr(raw: str) -> float:
    raw = raw.strip()
    if "/" in raw:
        num, den = raw.split("/", 1)
        return float(num) / float(den)
    return float(raw)


def _normalize_dice(raw: str) -> str:
    return re.sub(r"\s+", "", raw.lower().replace("d", "d"))


@dataclass
class ParsedSpanishStatBlock:
    name: str
    creature_type: str
    size: str
    alignment: str
    armor_class: int
    armor_detail: str
    hit_points: int
    hit_dice: str
    speed_walk: int
    ability_scores: dict[str, int]
    skill_bonuses: dict[str, int] = field(default_factory=dict)
    challenge_rating: float = 0.0
    traits: list[dict[str, str]] = field(default_factory=list)
    actions: list[dict[str, Any]] = field(default_factory=list)
    raw_text: str = ""


def extract_monster_block_from_page(page_text: str, monster_name: str) -> str:
    """Isolate one stat block from a PDF page that may contain lore and multiple monsters."""
    text = _normalize_text(page_text)
    target = monster_name.strip().upper()

    type_matches = list(_TYPE_LINE.finditer(text))
    if not type_matches:
        raise ValueError(f"No stat block type lines found on page for {monster_name!r}")

    start_index: int | None = None
    name_pattern = re.compile(rf"(?:^|\n)\s*{re.escape(target)}\s*(?:\n|$)", re.IGNORECASE | re.MULTILINE)
    for match in type_matches:
        prefix = text[: match.start()]
        name_matches = list(name_pattern.finditer(prefix))
        if not name_matches:
            continue
        candidate_start = name_matches[-1].start()
        if start_index is None or candidate_start > start_index:
            start_index = candidate_start
            chosen_type_start = match.start()

    if start_index is None:
        raise ValueError(f"Stat block for {monster_name!r} not found on page")

    end_index = len(text)
    for match in type_matches:
        if match.start() <= chosen_type_start:
            continue
        end_index = _header_line_before_type(text, match.start())
        break

    return text[start_index:end_index].strip()


def _header_line_before_type(text: str, type_line_start: int) -> int:
    """Return the start index of the ALL CAPS name line preceding a type line."""
    prefix = text[:type_line_start].rstrip("\n")
    if not prefix:
        return type_line_start
    last_newline = prefix.rfind("\n")
    header = prefix[last_newline + 1 :] if last_newline >= 0 else prefix
    header = header.strip()
    if header and header == header.upper() and re.match(r"^[A-ZÁÉÍÓÚÑ0-9 /\-'.]+$", header):
        return prefix.rfind(header)
    return type_line_start


def parse_spanish_stat_block(block_text: str) -> ParsedSpanishStatBlock:
    """Parse a single Spanish stat block into structured fields."""
    text = _normalize_text(block_text)
    type_match = _TYPE_LINE.search(text)
    if not type_match:
        raise ValueError("Missing creature type line")

    prefix = text[: type_match.start()].strip()
    name_lines = [line.strip() for line in prefix.splitlines() if line.strip()]
    name = name_lines[-1] if name_lines else "Monstruo"

    ac_match = _AC.search(text)
    hp_match = _HP.search(text)
    speed_match = _SPEED.search(text)
    cr_match = _CR.search(text)
    compact_text = re.sub(r"\s+", " ", text)
    ability_match = _ABILITY_SCORES.search(compact_text)
    if not all([ac_match, hp_match, speed_match, cr_match, ability_match]):
        raise ValueError("Incomplete stat block: missing AC, HP, speed, CR, or abilities")

    ability_scores = {
        full: int(ability_match.group(index * 2 + 1))
        for index, full in enumerate(_ABILITY_FULL)
    }

    skill_bonuses: dict[str, int] = {}
    skills_match = _SKILLS.search(text)
    if skills_match:
        for skill_name, bonus in re.findall(r"(\w+)\s*\+(\d+)", skills_match.group(1)):
            key = _SKILL_KEY_MAP.get(_slugify(skill_name))
            if key:
                skill_bonuses[key] = int(bonus)

    traits: list[dict[str, str]] = []
    actions_header = _SECTION_HEADERS.search(text)
    traits_text = text[cr_match.end() : actions_header.start() if actions_header else len(text)]
    for paragraph in re.split(r"\n\s*\n", traits_text.strip()):
        cleaned = " ".join(paragraph.split())
        if not cleaned or cleaned.upper().startswith(("SENTIDOS", "IDIOMAS", "HABILIDADES")):
            continue
        if ". " in cleaned:
            trait_name, trait_desc = cleaned.split(". ", 1)
            traits.append({"name": trait_name.strip(), "desc": trait_desc.strip()})
        else:
            traits.append({"name": cleaned, "desc": cleaned})

    actions: list[dict[str, Any]] = []
    if actions_header:
        actions_text = text[actions_header.end() :]
        next_section = _SECTION_HEADERS.search(actions_text)
        if next_section:
            actions_text = actions_text[: next_section.start()]
        actions_text = re.sub(r"\s+", " ", actions_text)
        for attack_match in _ATTACK.finditer(actions_text):
            dice_raw = _normalize_dice(attack_match.group("dice"))
            dice_match = re.match(r"(\d+)d(\d+)([+-]\d+)?", dice_raw)
            if not dice_match:
                continue
            damage_bonus = int(dice_match.group(3) or 0)
            actions.append(
                {
                    "name": attack_match.group("name").strip(),
                    "desc": attack_match.group(0).strip(),
                    "attacks": [
                        {
                            "to_hit_mod": int(attack_match.group("to_hit")),
                            "damage_die_count": int(dice_match.group(1)),
                            "damage_die_type": f"D{dice_match.group(2)}",
                            "damage_bonus": damage_bonus,
                            "damage_type": {"key": attack_match.group("damage_type")},
                        }
                    ],
                }
            )

    return ParsedSpanishStatBlock(
        name=name.title() if name.isupper() else name,
        creature_type=type_match.group("creature_type"),
        size=type_match.group("size"),
        alignment=type_match.group("alignment").strip(),
        armor_class=int(ac_match.group(1)),
        armor_detail=(ac_match.group(2) or "").strip(),
        hit_points=int(hp_match.group(1)),
        hit_dice=hp_match.group(2).strip(),
        speed_walk=int(speed_match.group(1)),
        ability_scores=ability_scores,
        skill_bonuses=skill_bonuses,
        challenge_rating=_parse_cr(cr_match.group(1)),
        traits=traits,
        actions=actions,
        raw_text=text,
    )


def parsed_to_open5e_creature(parsed: ParsedSpanishStatBlock) -> dict[str, Any]:
    """Convert parsed Spanish block to Open5e-like creature dict for MonsterSheetMapper."""
    return {
        "key": f"mm_edge_{_slugify(parsed.name)}",
        "name": parsed.name,
        "type": {"name": parsed.creature_type},
        "size": {"name": parsed.size},
        "alignment": parsed.alignment,
        "armor_class": parsed.armor_class,
        "armor_detail": parsed.armor_detail,
        "hit_points": parsed.hit_points,
        "hit_dice": parsed.hit_dice,
        "challenge_rating": parsed.challenge_rating,
        "ability_scores": parsed.ability_scores,
        "skill_bonuses": parsed.skill_bonuses,
        "traits": parsed.traits,
        "actions": parsed.actions,
    }


def append_source_provenance(sheet: dict[str, Any], source_label: str) -> dict[str, Any]:
    """Append visible source attribution to the sheet features block."""
    footer = f"Fuente: {source_label}"
    features = str(sheet.get("features_traits") or "").strip()
    sheet["features_traits"] = f"{features}\n\n{footer}".strip() if features else footer
    return sheet


def build_catalog_row_from_parsed(
    parsed: ParsedSpanishStatBlock,
    *,
    slug: str,
    source_document: str,
    source_label: str,
    system_id: str = "dnd5e",
) -> dict[str, Any]:
    """Build a system_monster_catalog row from a parsed Spanish stat block."""
    import uuid

    creature = parsed_to_open5e_creature(parsed)
    sheet = MonsterSheetMapper.map_creature(creature)
    sheet = append_source_provenance(sheet, source_label)

    narrative = build_narrative_template(creature)
    narrative["public_description"] = f"Un {parsed.name.lower()} del {source_label}."

    return {
        "id": uuid.uuid4(),
        "system_id": system_id,
        "slug": slug,
        "name": parsed.name,
        "name_normalized": normalize_monster_name(parsed.name),
        "challenge_rating": parsed.challenge_rating,
        "creature_type": parsed.creature_type,
        "size": parsed.size,
        "source_document": source_document,
        "source_label": source_label,
        "narrative_template": narrative,
        "sheet_template": sheet,
        "raw_stat_block": {
            "parser": "spanish_stat_block_parser",
            "source_document": source_document,
            "source_label": source_label,
            "parsed": {
                "name": parsed.name,
                "creature_type": parsed.creature_type,
                "size": parsed.size,
                "alignment": parsed.alignment,
                "armor_class": parsed.armor_class,
                "hit_points": parsed.hit_points,
                "challenge_rating": parsed.challenge_rating,
            },
            "raw_text": parsed.raw_text,
        },
    }


def validate_parsed_sheet(parsed: ParsedSpanishStatBlock, *, source_label: str) -> Dnd5eSheet:
    creature = parsed_to_open5e_creature(parsed)
    sheet = append_source_provenance(MonsterSheetMapper.map_creature(creature), source_label)
    return Dnd5eSheet.model_validate(sheet)
