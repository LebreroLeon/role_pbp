"""Parse Spanish D&D 5e stat blocks from Edge manual PDF text."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any

from app.rules.dnd5e.damage_types import normalize_damage_type
from app.rules.dnd5e.monster_sheet_mapper import (
    MonsterSheetMapper,
    build_creature_concept,
    build_narrative_template,
    format_challenge_rating_display,
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
    "conocimientoarcano": "arcana",
    "naturaleza": "nature",
    "religion": "religion",
    "medicina": "medicine",
    "supervivencia": "survival",
}
_SKILL_ES_NAMES: list[tuple[str, str]] = [
    ("conocimiento arcano", "arcana"),
    ("juego de manos", "sleight_of_hand"),
    ("trato con animales", "animal_handling"),
    ("sigilo", "stealth"),
    ("atletismo", "athletics"),
    ("acrobacias", "acrobatics"),
    ("percepción", "perception"),
    ("percepcion", "perception"),
    ("perspicacia", "insight"),
    ("investigación", "investigation"),
    ("investigacion", "investigation"),
    ("engaño", "deception"),
    ("engano", "deception"),
    ("intimidación", "intimidation"),
    ("intimidacion", "intimidation"),
    ("persuasión", "persuasion"),
    ("persuasion", "persuasion"),
    ("historia", "history"),
    ("naturaleza", "nature"),
    ("religión", "religion"),
    ("religion", "religion"),
    ("medicina", "medicine"),
    ("supervivencia", "survival"),
    ("arcano", "arcana"),
]
_SAVE_ABBR = {
    "FUE": "strength",
    "DES": "dexterity",
    "CON": "constitution",
    "INT": "intelligence",
    "SAB": "wisdom",
    "CAR": "charisma",
}

_SIZE_WORDS = frozenset(
    {
        "pequeno",
        "pequena",
        "mediano",
        "mediana",
        "grande",
        "enorme",
        "gargantuesca",
        "gargantuesco",
        "gigante",
        "diminuto",
        "minusculo",
        "minuculo",
        "colosal",
    }
)
_TYPE_LINE_WITH_SUBTYPE = re.compile(
    r"^(?P<creature_type>\w+)[ \t]+(?P<size>\w+)[ \t]*\([^)]+\),[ \t]*(?P<alignment>.+)$",
    re.MULTILINE | re.IGNORECASE,
)
_TYPE_LINE_SIMPLE = re.compile(
    r"^(?P<creature_type>\w+)[ \t]+(?P<size>\w+),?[ \t]*(?P<alignment>.+)$",
    re.MULTILINE | re.IGNORECASE,
)
_AC = re.compile(
    r"(?:Clase|Categor[ií]a) de Armadura:?\s*(\d+)(?:\s*\(([^)]+)\))?",
    re.IGNORECASE,
)
_HP = re.compile(r"Puntos de [Gg]olpe:?\s*(\d+)\s*\(([^)]+)\)", re.IGNORECASE)
_SPEED = re.compile(r"Velocidad:?\s*([O0\d]+)", re.IGNORECASE)
_CR = re.compile(r"Desaf[ií]o:?\s*([\d/]+)(?:\s*\([\d,]+\s*(?:PX|XP)\))?", re.IGNORECASE)
_SKILLS = re.compile(
    r"Habilidades:?\s*(.+?)(?=\n(?:Inmunidad|Sentidos|Idiomas|Desaf[ií]o|Tiradas)|\Z)",
    re.IGNORECASE | re.DOTALL,
)
_SAVING_THROWS = re.compile(
    r"Tiradas de [Ss]alvaci[oó]n:?\s*(.+?)(?:\n|Habilidades|Sentidos|Idiomas|Desaf[ií]o|Inmunidad|$)",
    re.IGNORECASE | re.DOTALL,
)
_SENSES = re.compile(r"Sentidos:?\s*(.+?)(?:\n|Idiomas|Desaf[ií]o|Inmunidad|$)", re.IGNORECASE | re.DOTALL)
_LANGUAGES = re.compile(r"Idiomas:?\s*(.+?)(?:\n|Desaf[ií]o|Inmunidad|Bonificador|$)", re.IGNORECASE | re.DOTALL)
_CONDITION_IMMUNITIES = re.compile(
    r"Inmunidad a estados:?\s*(.+?)(?:\n|Sentidos|Idiomas|Desaf[ií]o|$)",
    re.IGNORECASE | re.DOTALL,
)
_PROFICIENCY_BONUS = re.compile(r"Bonificador por competencia:?\s*\+(\d+)", re.IGNORECASE)
_CR_XP_NOISE = re.compile(r"^\([\d,]+\s*(?:PX|XP)\)\.?\s*$", re.IGNORECASE)
_ABILITY_SCORES = re.compile(
    r"(\d+)\s*\(([+-]?\d+)\)\s+"
    r"(\d+)\s*\(([+-]?\d+)\)\s+"
    r"(\d+)\s*\(([+-]?\d+)\)\s+"
    r"(\d+)\s*\(([+-]?\d+)\)\s+"
    r"(\d+)\s*\(([+-]?\d+)\)\s+"
    r"(\d+)\s*\(([+-]?\d+)\)",
)
_DAMAGE_TYPE_WORD = (
    r"contundente|cortante|perforante|ps[ií]quico|[áa]cido|fuego|fr[ií]o|"
    r"el[eé]ctrico|necr[oó]tico|radiante|trueno|veneno|contun|ps[ií]quic"
)
_ATTACK = re.compile(
    r"Ataque[^:]*:\s*\+?\s*(?P<to_hit>\d+)\s+a\s+impactar.*?"
    r"(?:Impacto|Al impactar):\s*\d+\s*\((?P<dice>[^)]+)\)\s*"
    rf"(?:de\s+da[ñn]o\s+)?(?P<damage_type>{_DAMAGE_TYPE_WORD}|\w+)",
    re.IGNORECASE | re.DOTALL,
)
_DAMAGE_ROLL = re.compile(
    rf"(?P<avg>\d+)\s*\((?P<dice>[^)]+)\)\s*(?:de\s+)?daño\s+(?P<damage_type>{_DAMAGE_TYPE_WORD})",
    re.IGNORECASE,
)
_SPELLCASTING_NAME = re.compile(
    r"lanzamiento\s+(?:innato\s+)?de\s+conjuros",
    re.IGNORECASE,
)
_ACTION_BLOCK = re.compile(
    r"(?:^|\n)"
    r"([A-ZÁÉÍÓÚÑ][^\n.]{1,60}?)"
    r"\.\s+",
    re.MULTILINE,
)
_FEATURE_NAME_INVALID = re.compile(
    r"\b(?:CD|tirada|salvaci[oó]n|criatura|objetivo|da[ñn]o|turno|pies|metr|voluntad|d[ií]a)\b",
    re.IGNORECASE,
)
_ABILITY_SCORE_PAIR = re.compile(r"(\d+)\s*\([+-]?\d+\)")
_ACTION_SECTION_SPECS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("legendary", re.compile(r"^ACCIONES\s+LEGENDARIAS\s*$", re.MULTILINE | re.IGNORECASE)),
    ("bonus_actions", re.compile(r"^ACCIONES\s+ADICIONALES\s*$", re.MULTILINE | re.IGNORECASE)),
    ("reactions", re.compile(r"^REACCIONES\s*$", re.MULTILINE | re.IGNORECASE)),
    ("actions", re.compile(r"^ACCIONES\s*$", re.MULTILINE | re.IGNORECASE)),
)
_TRAIT_KIND_METADATA = frozenset({"Sentidos", "Idiomas", "Inmunidad a estados", "Velocidad"})
_PAGE_FOOTER_NOISE = re.compile(
    r"\d{2,4}\s+CAP[IÍ]TULO.*?$|^[•·]\s*$",
    re.IGNORECASE | re.MULTILINE | re.DOTALL,
)
_OCR_GARBAGE_LINE = re.compile(
    r"^[/\\|_'\"0-9\s]{0,8}(?:[A-Za-z]{1,4}[\-/\\|_'\"]{0,3})+[A-Za-z0-9\s\-_/\\|.'\"]{0,24}$"
    r"|rendimos"
    r"|en goblin",
    re.IGNORECASE,
)
_OTHER_MONSTER_HEADER = re.compile(
    r"^[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ0-9 /\-'.]{2,}$",
)


def _normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFKC", value)
    text = text.replace("{", "(").replace("}", ")")
    return text.replace("Ü", "O").replace("ü", "o")


def _normalize_header_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().upper())
    without_accents = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return without_accents.replace("Ü", "O")


def _iter_type_line_matches(text: str):
    seen_spans: set[int] = set()
    for pattern in (_TYPE_LINE_WITH_SUBTYPE, _TYPE_LINE_SIMPLE):
        for match in pattern.finditer(text):
            if match.start() in seen_spans:
                continue
            if pattern is _TYPE_LINE_SIMPLE and _slugify(match.group("size")) not in _SIZE_WORDS:
                continue
            seen_spans.add(match.start())
            yield match


def _parse_speed(raw: str) -> int:
    normalized = raw.strip().upper().replace("O", "0")
    digit_match = re.search(r"\d+", normalized)
    if not digit_match:
        raise ValueError(f"Could not parse speed from {raw!r}")
    return int(digit_match.group(0))


def _parse_ability_scores_from_text(text: str) -> dict[str, int]:
    compact_text = re.sub(r"\s+", " ", text)
    ability_match = _ABILITY_SCORES.search(compact_text)
    if ability_match:
        return {
            full: int(ability_match.group(index * 2 + 1))
            for index, full in enumerate(_ABILITY_FULL)
        }

    scores: dict[str, int] = {}
    for abbr, full in zip(_ABILITY_ES, _ABILITY_FULL):
        label_match = re.search(
            rf"{abbr}\s+(\d+)\s*\([+-]?\d+\)",
            text,
            re.IGNORECASE | re.MULTILINE,
        )
        if label_match:
            scores[full] = int(label_match.group(1))

    if len(scores) == 6:
        return scores

    block_match = re.search(
        r"FUE\s+DES\s+CON\s+INT\s+SAB\s+CAR\s+((?:\d+\s*\([+-]?\d+\)\s*){6})",
        compact_text,
        re.IGNORECASE,
    )
    if block_match:
        values = _ABILITY_SCORE_PAIR.findall(block_match.group(1))
        if len(values) == 6:
            return {full: int(values[index]) for index, full in enumerate(_ABILITY_FULL)}

    raise ValueError("Could not parse ability scores from stat block")


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


def _normalize_damage_type_word(raw: str) -> str:
    slug = _slugify(raw)
    aliases = {
        "contun": "contundente",
        "psiquic": "psiquico",
        "acido": "acido",
    }
    return aliases.get(slug, raw)


def _fix_ocr_skill_segment(segment: str) -> str:
    fixed = re.sub(r"\+\s*(\d)\s+O\b", lambda m: f"+{m.group(1)}0", segment)
    fixed = re.sub(r"(\d)\s+O\b", lambda m: f"{m.group(1)}0", fixed)
    return fixed


def _parse_skill_bonuses(text: str) -> dict[str, int]:
    skills_match = _SKILLS.search(text)
    if not skills_match:
        return {}

    segment = _fix_ocr_skill_segment(skills_match.group(1))
    bonuses: dict[str, int] = {}
    for label, key in sorted(_SKILL_ES_NAMES, key=lambda item: -len(item[0])):
        pattern = rf"{re.escape(label)}\s*\+\s*(\d+)"
        match = re.search(pattern, segment, re.IGNORECASE)
        if match:
            bonuses[key] = int(match.group(1))

    if not bonuses:
        for skill_name, bonus in re.findall(r"(\w+)\s*\+(\d+)", segment):
            key = _SKILL_KEY_MAP.get(_slugify(skill_name))
            if key:
                bonuses[key] = int(bonus)
    return bonuses


def _parse_saving_throw_bonuses(text: str) -> dict[str, int]:
    match = _SAVING_THROWS.search(text)
    if not match:
        return {}

    segment = match.group(1)
    bonuses: dict[str, int] = {}
    for abbr, full in _SAVE_ABBR.items():
        save_match = re.search(rf"\b{abbr}\s*\+\s*(\d+)", segment, re.IGNORECASE)
        if save_match:
            bonuses[full] = int(save_match.group(1))
    return bonuses


def _is_spellcasting_feature(name: str, desc: str = "") -> bool:
    combined = f"{name} {desc}"
    return bool(_SPELLCASTING_NAME.search(combined))


def _trait_kind(name: str, desc: str = "") -> str:
    if name in _TRAIT_KIND_METADATA:
        return "metadata"
    if _is_spellcasting_feature(name, desc):
        return "spellcasting"
    return "trait"


def _tag_trait(trait: dict[str, str]) -> dict[str, str]:
    name = str(trait.get("name", "")).strip()
    desc = str(trait.get("desc", "")).strip()
    tagged = dict(trait)
    tagged["kind"] = _trait_kind(name, desc)
    return tagged


def _find_action_sections(text: str) -> list[tuple[str, int, int]]:
    """Return ordered (section_key, start, end) slices for action areas."""
    matches: list[tuple[str, int]] = []
    for section_key, pattern in _ACTION_SECTION_SPECS:
        for match in pattern.finditer(text):
            matches.append((section_key, match.start()))

    if not matches:
        return []

    matches.sort(key=lambda item: item[1])
    deduped: list[tuple[str, int]] = []
    seen_positions: set[int] = set()
    for section_key, start in matches:
        if start in seen_positions:
            continue
        seen_positions.add(start)
        deduped.append((section_key, start))

    sections: list[tuple[str, int, int]] = []
    for index, (section_key, start) in enumerate(deduped):
        header_match = None
        for _, pattern in _ACTION_SECTION_SPECS:
            header_match = pattern.search(text, start)
            if header_match and header_match.start() == start:
                break
        content_start = header_match.end() if header_match else start
        end = deduped[index + 1][1] if index + 1 < len(deduped) else len(text)
        sections.append((section_key, content_start, end))
    return sections


def _first_action_section_start(text: str) -> int | None:
    positions: list[int] = []
    for _, pattern in _ACTION_SECTION_SPECS:
        for match in pattern.finditer(text):
            positions.append(match.start())
    return min(positions) if positions else None


def _format_damage_summary(block: str) -> str:
    rolls = list(_DAMAGE_ROLL.finditer(block))
    if not rolls:
        return ""
    parts: list[str] = []
    for roll in rolls:
        dice = _normalize_dice(roll.group("dice"))
        damage_type = _normalize_damage_type_word(roll.group("damage_type"))
        parts.append(f"{dice} {damage_type}")
    return " + ".join(parts)


def _parse_attack_payload(block: str) -> list[dict[str, Any]]:
    attack_match = _ATTACK.search(block)
    if not attack_match:
        return []

    dice_raw = _normalize_dice(attack_match.group("dice"))
    dice_match = re.match(r"(\d+)d(\d+)([+-]\d+)?", dice_raw)
    if not dice_match:
        return []

    damage_bonus = int(dice_match.group(3) or 0)
    damage_type = _normalize_damage_type_word(attack_match.group("damage_type"))
    payload: dict[str, Any] = {
        "to_hit_mod": int(attack_match.group("to_hit")),
        "damage_die_count": int(dice_match.group(1)),
        "damage_die_type": f"D{dice_match.group(2)}",
        "damage_bonus": damage_bonus,
        "damage_type": {"key": damage_type},
    }
    extra_summary = _format_damage_summary(block)
    primary_summary = f"{dice_match.group(1)}d{dice_match.group(2)}"
    if damage_bonus:
        primary_summary += f"{damage_bonus:+d}"
    if extra_summary and extra_summary != f"{primary_summary} {damage_type}":
        payload["damage_summary"] = extra_summary
    return [payload]


def _strip_trait_metadata_prefix(text: str) -> str:
    cleaned = re.sub(r"^\([\d,]+\s*(?:PX|XP)\)\.?\s*", "", text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(
        r"^Bonificador por competencia:\s*\+\d+\.?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    return cleaned.strip()


def _looks_like_feature_name(name: str) -> bool:
    cleaned = " ".join(name.split())
    if len(cleaned) < 3 or len(cleaned) > 60:
        return False
    if _FEATURE_NAME_INVALID.search(cleaned):
        return False
    if cleaned.lower().startswith(("el ", "la ", "los ", "las ", "una ", "un ", "cada ", "si ", "cuando ")):
        return False
    return True


def _split_traits(traits_text: str) -> list[dict[str, str]]:
    text = _strip_trait_metadata_prefix(traits_text)
    if not text:
        return []

    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", text) if paragraph.strip()]
    if len(paragraphs) == 1:
        flattened = " ".join(paragraphs[0].split())
        parts = re.split(
            r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ][A-Za-záéíóúñÁÉÍÓÚÑ\s\-]+(?:\([^)]+\))?\.\s)",
            flattened,
        )
        paragraphs = parts if len(parts) > 1 else paragraphs

    traits: list[dict[str, str]] = []
    for paragraph in paragraphs:
        cleaned = " ".join(paragraph.split())
        if not cleaned or _CR_XP_NOISE.match(cleaned):
            continue
        if re.match(r"^\([\d,]+\s*(?:PX|XP)\)$", cleaned, re.IGNORECASE):
            continue
        if re.match(r"^Bonificador por competencia", cleaned, re.IGNORECASE):
            continue
        if ". " in cleaned:
            trait_name, trait_desc = cleaned.split(". ", 1)
            if re.match(r"^\([\d,]+\s*(?:PX|XP)\)$", trait_name.strip(), re.IGNORECASE):
                cleaned = trait_desc
                if ". " in cleaned:
                    trait_name, trait_desc = cleaned.split(". ", 1)
                else:
                    trait_name, trait_desc = cleaned, cleaned
            if not _looks_like_feature_name(trait_name):
                if traits:
                    traits[-1]["desc"] = f"{traits[-1]['desc']} {cleaned}".strip()
                else:
                    traits.append(_tag_trait({"name": cleaned, "desc": cleaned}))
                continue
            traits.append(_tag_trait({"name": trait_name.strip(), "desc": trait_desc.strip()}))
        else:
            traits.append(_tag_trait({"name": cleaned, "desc": cleaned}))
    return traits


def _normalize_dice(raw: str) -> str:
    return re.sub(r"\s+", "", raw.lower().replace("d", "d"))


def _iter_action_blocks(actions_text: str) -> list[tuple[str, str]]:
    text = _PAGE_FOOTER_NOISE.sub("", actions_text.strip())
    text = re.sub(r"[•·]\s*", "", text)
    starts = [
        match
        for match in _ACTION_BLOCK.finditer(text)
        if _looks_like_feature_name(match.group(1).strip())
    ]
    blocks: list[tuple[str, str]] = []
    for index, match in enumerate(starts):
        name = match.group(1).strip()
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        blocks.append((name, text[match.start() : end].strip()))
    return blocks


def _parse_actions_from_section(
    actions_text: str,
    *,
    section: str = "actions",
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Parse one action section; spellcasting blocks are returned as traits."""
    actions: list[dict[str, Any]] = []
    spell_traits: list[dict[str, str]] = []
    for name, block in _iter_action_blocks(actions_text):
        if _is_spellcasting_feature(name, block):
            spell_traits.append(_tag_trait({"name": name, "desc": block}))
            continue

        attacks = _parse_attack_payload(block)
        action_entry: dict[str, Any] = {
            "name": name,
            "desc": block,
            "section": section,
            "attacks": attacks,
        }
        if attacks and attacks[0].get("damage_summary"):
            action_entry["damage_summary"] = attacks[0]["damage_summary"]
        actions.append(action_entry)
    return actions, spell_traits


def _metadata_traits(text: str) -> list[dict[str, str]]:
    traits: list[dict[str, str]] = []
    senses_match = _SENSES.search(text)
    if senses_match:
        traits.append(_tag_trait({"name": "Sentidos", "desc": " ".join(senses_match.group(1).split())}))
    languages_match = _LANGUAGES.search(text)
    if languages_match:
        traits.append(_tag_trait({"name": "Idiomas", "desc": " ".join(languages_match.group(1).split())}))
    immunities_match = _CONDITION_IMMUNITIES.search(text)
    if immunities_match:
        traits.append(
            _tag_trait(
                {
                    "name": "Inmunidad a estados",
                    "desc": " ".join(immunities_match.group(1).split()),
                }
            )
        )
    speed_match = _SPEED.search(text)
    if speed_match:
        traits.append(_tag_trait({"name": "Velocidad", "desc": speed_match.group(0).strip()}))
    return traits


@dataclass
class ParsedSpanishStatBlock:
    name: str
    creature_type: str
    size: str
    alignment: str
    type_line: str
    armor_class: int
    armor_detail: str
    hit_points: int
    hit_dice: str
    speed_walk: int
    ability_scores: dict[str, int]
    skill_bonuses: dict[str, int] = field(default_factory=dict)
    saving_throw_bonuses: dict[str, int] = field(default_factory=dict)
    proficiency_bonus: int | None = None
    challenge_rating: float = 0.0
    challenge_rating_raw: str = ""
    traits: list[dict[str, str]] = field(default_factory=list)
    actions: list[dict[str, Any]] = field(default_factory=list)
    raw_text: str = ""


def _stat_block_start_index(page_text: str, monster_name: str) -> int | None:
    text = _normalize_text(page_text)
    target = _normalize_header_name(monster_name)
    type_matches = list(_iter_type_line_matches(text))
    if not type_matches:
        return None

    name_pattern = re.compile(
        rf"(?:^|\n)\s*{re.escape(target)}\s*(?:\n|$)",
        re.IGNORECASE | re.MULTILINE,
    )
    start_index: int | None = None
    for match in type_matches:
        prefix = text[: match.start()]
        name_matches = list(name_pattern.finditer(prefix))
        if not name_matches:
            continue
        candidate_start = name_matches[-1].start()
        if start_index is None or candidate_start > start_index:
            start_index = candidate_start
    return start_index


def _is_lore_noise_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if re.fullmatch(r"\d{1,4}", stripped):
        return True
    if _OCR_GARBAGE_LINE.search(stripped):
        return True
    if re.search(r"cap[ií]tulo|bestiario", stripped, re.IGNORECASE):
        return True
    if re.fullmatch(r"[\s/W\\|_\-\.'\"0-9]+", stripped):
        return True
    return False


def _clean_lore_text(
    raw_text: str,
    *,
    monster_name: str,
    stop_at_monster_header: bool = False,
) -> str:
    target = monster_name.strip().upper()
    paragraphs: list[str] = []
    current: list[str] = []

    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        if _is_lore_noise_line(stripped):
            continue
        if stop_at_monster_header and stripped.upper() == target:
            break
        if stop_at_monster_header and _TYPE_LINE_WITH_SUBTYPE.match(stripped):
            break
        if stop_at_monster_header and _TYPE_LINE_SIMPLE.match(stripped):
            size_slug = _slugify(stripped.split(",", 1)[0].split()[-1] if "," in stripped else "")
            if size_slug in _SIZE_WORDS:
                break
        if stop_at_monster_header and _OTHER_MONSTER_HEADER.match(stripped) and stripped.upper() != target:
            break
        current.append(stripped)

    if current:
        paragraphs.append(" ".join(current))

    return "\n\n".join(paragraph for paragraph in paragraphs if paragraph.strip())


def _first_stat_block_start(text: str, monster_name: str) -> int | None:
    return _stat_block_start_index(text, monster_name)


def _foreign_stat_block_starts(text: str, monster_name: str) -> list[int]:
    target = _normalize_header_name(monster_name)
    starts: list[int] = []
    type_matches = list(_iter_type_line_matches(text))
    name_header = re.compile(
        r"(?:^|\n)\s*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ0-9 /\-'.]+)\s*(?:\n|$)",
        re.MULTILINE,
    )
    for match in type_matches:
        prefix = text[: match.start()]
        headers = list(name_header.finditer(prefix))
        if not headers:
            continue
        header_name = headers[-1].group(1).strip().upper()
        if header_name != target:
            starts.append(headers[-1].start())
    return starts


def _extract_lore_from_page(page_text: str, *, monster_name: str) -> str:
    text = _normalize_text(page_text)
    foreign_starts = _foreign_stat_block_starts(text, monster_name)
    if foreign_starts and foreign_starts[0] <= 40:
        return ""
    end_index = min(foreign_starts) if foreign_starts else len(text)
    own_start = _first_stat_block_start(text, monster_name)
    if own_start is not None:
        end_index = min(end_index, own_start)
    excerpt = text[:end_index]
    return _clean_lore_text(
        excerpt,
        monster_name=monster_name,
        stop_at_monster_header=own_start is not None,
    )


def extract_monster_lore_from_pages(
    pages: dict[int, str],
    *,
    stat_page: int,
    monster_name: str,
    lookback_pages: int = 2,
) -> str:
    """Extract descriptive lore from pages preceding (and prefix of) the stat block page."""
    chunks: list[str] = []

    stat_page_text = pages.get(stat_page)
    if stat_page_text:
        normalized = _normalize_text(stat_page_text)
        start_index = _stat_block_start_index(normalized, monster_name)
        if start_index and start_index > 0:
            prefix = _clean_lore_text(
                normalized[:start_index],
                monster_name=monster_name,
                stop_at_monster_header=True,
            )
            if prefix and len(prefix) >= 40:
                chunks.append(prefix)

    if not chunks:
        for page_num in range(stat_page - 1, max(0, stat_page - lookback_pages - 1), -1):
            page_text = pages.get(page_num)
            if not page_text:
                continue
            cleaned = _extract_lore_from_page(page_text, monster_name=monster_name)
            if cleaned and len(cleaned) >= 40:
                chunks.insert(0, cleaned)
                break

    if not chunks:
        return ""

    deduped: list[str] = []
    for chunk in chunks:
        if chunk not in deduped:
            deduped.append(chunk)

    merged = "\n\n".join(deduped)
    merged = re.sub(r"\n{3,}", "\n\n", merged).strip()
    return merged


def extract_monster_block_from_page(page_text: str, monster_name: str) -> str:
    """Isolate one stat block from a PDF page that may contain lore and multiple monsters."""
    text = _normalize_text(page_text)
    target = _normalize_header_name(monster_name)

    type_matches = list(_iter_type_line_matches(text))
    if not type_matches:
        raise ValueError(f"No stat block type lines found on page for {monster_name!r}")

    start_index: int | None = None
    name_pattern = re.compile(
        rf"(?:^|\n)\s*{re.escape(target)}\s*(?:\n|$)",
        re.IGNORECASE | re.MULTILINE,
    )
    chosen_type_start = 0
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
    type_match = next(iter(_iter_type_line_matches(text)), None)
    if not type_match:
        raise ValueError("Missing creature type line")

    prefix = text[: type_match.start()].strip()
    name_lines = [line.strip() for line in prefix.splitlines() if line.strip()]
    name = name_lines[-1] if name_lines else "Monstruo"

    ac_match = _AC.search(text)
    hp_match = _HP.search(text)
    speed_match = _SPEED.search(text)
    cr_match = _CR.search(text)
    if not all([ac_match, hp_match, speed_match, cr_match]):
        raise ValueError("Incomplete stat block: missing AC, HP, speed, or CR")

    ability_scores = _parse_ability_scores_from_text(text)

    skill_bonuses = _parse_skill_bonuses(text)
    saving_throw_bonuses = _parse_saving_throw_bonuses(text)
    proficiency_match = _PROFICIENCY_BONUS.search(text)
    proficiency_bonus = int(proficiency_match.group(1)) if proficiency_match else None

    first_action_start = _first_action_section_start(text)
    traits_text = text[cr_match.end() : first_action_start if first_action_start is not None else len(text)]
    for pattern in (_SAVING_THROWS, _SKILLS, _SENSES, _LANGUAGES, _CONDITION_IMMUNITIES, _PROFICIENCY_BONUS):
        traits_text = pattern.sub("", traits_text)
    traits = _split_traits(traits_text)
    traits = _metadata_traits(text) + traits

    actions: list[dict[str, Any]] = []
    for section_key, content_start, content_end in _find_action_sections(text):
        section_actions, spell_traits = _parse_actions_from_section(
            text[content_start:content_end],
            section=section_key,
        )
        actions.extend(section_actions)
        traits.extend(spell_traits)

    return ParsedSpanishStatBlock(
        name=name.title() if name.isupper() else name,
        creature_type=type_match.group("creature_type"),
        size=type_match.group("size"),
        alignment=type_match.group("alignment").strip(),
        type_line=type_match.group(0).strip(),
        armor_class=int(ac_match.group(1)),
        armor_detail=(ac_match.group(2) or "").strip(),
        hit_points=int(hp_match.group(1)),
        hit_dice=hp_match.group(2).strip(),
        speed_walk=_parse_speed(speed_match.group(1)),
        ability_scores=ability_scores,
        skill_bonuses=skill_bonuses,
        saving_throw_bonuses=saving_throw_bonuses,
        proficiency_bonus=proficiency_bonus,
        challenge_rating=_parse_cr(cr_match.group(1)),
        challenge_rating_raw=format_challenge_rating_display(
            _parse_cr(cr_match.group(1)),
            raw=cr_match.group(1),
        ),
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
        "type_line": parsed.type_line,
        "armor_class": parsed.armor_class,
        "armor_detail": parsed.armor_detail,
        "hit_points": parsed.hit_points,
        "hit_dice": parsed.hit_dice,
        "speed": {"walk": parsed.speed_walk, "unit": "feet"},
        "challenge_rating": parsed.challenge_rating,
        "challenge_rating_display": parsed.challenge_rating_raw,
        "ability_scores": parsed.ability_scores,
        "skill_bonuses": parsed.skill_bonuses,
        "saving_throws": parsed.saving_throw_bonuses,
        "proficiency_bonus": parsed.proficiency_bonus,
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
    lore_text: str = "",
) -> dict[str, Any]:
    """Build a system_monster_catalog row from a parsed Spanish stat block."""
    import uuid

    creature = parsed_to_open5e_creature(parsed)
    if lore_text.strip():
        creature["public_description"] = lore_text.strip()
    sheet = MonsterSheetMapper.map_creature(creature)
    sheet = append_source_provenance(sheet, source_label)

    narrative = build_narrative_template(creature)
    if lore_text.strip():
        narrative["public_description"] = lore_text.strip()
    else:
        narrative["public_description"] = (
            f"Un {parsed.name.lower()} ({build_creature_concept(creature).lower()}) "
            f"del {source_label}."
        )

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
                "type_line": parsed.type_line,
                "armor_class": parsed.armor_class,
                "hit_points": parsed.hit_points,
                "hit_dice": parsed.hit_dice,
                "challenge_rating": parsed.challenge_rating,
                "challenge_rating_display": parsed.challenge_rating_raw,
            },
            "raw_text": parsed.raw_text,
            "lore_text": lore_text.strip(),
        },
    }


def validate_parsed_sheet(parsed: ParsedSpanishStatBlock, *, source_label: str) -> Dnd5eSheet:
    creature = parsed_to_open5e_creature(parsed)
    sheet = append_source_provenance(MonsterSheetMapper.map_creature(creature), source_label)
    return Dnd5eSheet.model_validate(sheet)
