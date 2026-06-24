from __future__ import annotations

import re
import unicodedata

DND5E_DAMAGE_TYPE_SLUGS: frozenset[str] = frozenset(
    {
        "contundente",
        "cortante",
        "perforante",
        "acido",
        "frio",
        "fuego",
        "relampago",
        "trueno",
        "veneno",
        "fuerza",
        "necrotico",
        "psiquico",
        "radiante",
    }
)

DAMAGE_TYPE_ALIASES: dict[str, str] = {
    "bludgeoning": "contundente",
    "slashing": "cortante",
    "piercing": "perforante",
    "acid": "acido",
    "cold": "frio",
    "fire": "fuego",
    "lightning": "relampago",
    "thunder": "trueno",
    "poison": "veneno",
    "force": "fuerza",
    "necrotic": "necrotico",
    "psychic": "psiquico",
    "radiant": "radiante",
    "contundente": "contundente",
    "cortante": "cortante",
    "perforante": "perforante",
    "ácido": "acido",
    "acido": "acido",
    "frío": "frio",
    "frio": "frio",
    "fuego": "fuego",
    "relámpago": "relampago",
    "relampago": "relampago",
    "trueno": "trueno",
    "veneno": "veneno",
    "fuerza": "fuerza",
    "necrótico": "necrotico",
    "necrotico": "necrotico",
    "psíquico": "psiquico",
    "psiquico": "psiquico",
    "radiante": "radiante",
}


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().lower())
    without_accents = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return re.sub(r"[\s_-]+", "", without_accents)


PLACEHOLDER_DAMAGE_TYPES: frozenset[str] = frozenset({"sin tipo", "untyped", "sintype", "unknown"})


def resolve_damage_type_slug(raw: str | None) -> str | None:
    """Map a damage type to a canonical slug, or None when unknown/untyped."""
    if not raw or not str(raw).strip():
        return None
    normalized = str(raw).strip().lower()
    if normalized in PLACEHOLDER_DAMAGE_TYPES:
        return None
    key = _slugify(str(raw))
    if key in DAMAGE_TYPE_ALIASES:
        return DAMAGE_TYPE_ALIASES[key]
    if key in DND5E_DAMAGE_TYPE_SLUGS:
        return key
    return None


def normalize_damage_type(raw: str | None, *, default: str = "contundente") -> str:
    slug = resolve_damage_type_slug(raw)
    if slug is not None:
        return slug
    if not raw or not str(raw).strip():
        return default
    return default
