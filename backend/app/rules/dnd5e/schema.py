import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.rules.dnd5e.damage_types import DND5E_DAMAGE_TYPE_SLUGS, normalize_damage_type


class AbilityScores(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    str: int = Field(default=10, ge=1, le=30)
    dex: int = Field(default=10, ge=1, le=30)
    con: int = Field(default=10, ge=1, le=30)
    intelligence: int = Field(default=10, ge=1, le=30, validation_alias="int", serialization_alias="int")
    wis: int = Field(default=10, ge=1, le=30)
    cha: int = Field(default=10, ge=1, le=30)

    def score(self, ability: str) -> int:
        key = ability.strip().lower()
        if key == "int":
            return self.intelligence
        return getattr(self, key)


class SkillEntry(BaseModel):
    name: str
    proficient: bool = False
    expertise: bool = False


class HpBlock(BaseModel):
    max: int = Field(default=10, ge=0)
    current: int = Field(default=10, ge=0)
    temp: int = Field(default=0, ge=0)


class DeathSavesBlock(BaseModel):
    successes: int = Field(default=0, ge=0, le=3)
    failures: int = Field(default=0, ge=0, le=3)


class CurrencyBlock(BaseModel):
    cp: int = Field(default=0, ge=0)
    sp: int = Field(default=0, ge=0)
    ep: int = Field(default=0, ge=0)
    gp: int = Field(default=0, ge=0)
    pp: int = Field(default=0, ge=0)


def parse_class_level(combined: str) -> tuple[str, int]:
    trimmed = combined.strip()
    if not trimmed:
        return "", 1
    match = re.match(r"^(.+?)\s+(\d+)\s*$", trimmed)
    if match:
        level = max(1, min(20, int(match.group(2))))
        return match.group(1).strip(), level
    return trimmed, 1


def normalize_sheet_identity(raw: object) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {"class": "", "level": 1, "background": "", "race": "", "alignment": ""}

    data = dict(raw)
    character_class = str(data.get("class", data.get("class_", "")) or "").strip()
    level_raw = data.get("level")
    level = level_raw if isinstance(level_raw, int) else None

    if not character_class and level is None and "class_level" in data:
        character_class, level = parse_class_level(str(data.get("class_level", "")))

    if level is None:
        level = 1
    level = max(1, min(20, int(level)))

    return {
        "class": character_class,
        "level": level,
        "background": str(data.get("background", "") or ""),
        "race": str(data.get("race", "") or ""),
        "alignment": str(data.get("alignment", "") or ""),
    }


class SheetIdentityBlock(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    class_: str = Field(default="", alias="class")
    level: int = Field(default=1, ge=1, le=20)
    background: str = ""
    race: str = ""
    alignment: str = ""

    @model_validator(mode="before")
    @classmethod
    def migrate_class_level(cls, data: object) -> object:
        if isinstance(data, dict):
            return normalize_sheet_identity(data)
        return data


class RoleplayBlock(BaseModel):
    personality_traits: str = ""
    ideals: str = ""
    bonds: str = ""
    flaws: str = ""


def _ability_modifier(score: int) -> int:
    return (score - 10) // 2


def _normalize_attack_entry(
    attack: dict[str, Any],
    *,
    abilities: dict[str, Any],
    proficiency_bonus: int,
) -> dict[str, Any]:
    if "damage_dice" in attack and "damage_type" in attack:
        return attack

    damage = attack.get("damage")
    damage_dice = attack.get("damage_dice")
    damage_type = attack.get("damage_type")
    if damage_dice is None and isinstance(damage, dict):
        damage_dice = damage.get("dice", "1d4")
    if damage_type is None and isinstance(damage, dict):
        damage_type = damage.get("type", "contundente")

    ability = str(attack.get("ability", "str")).strip().lower()
    proficient = bool(attack.get("proficient", False))
    ability_score = abilities.get(ability, 10)
    ability_mod = _ability_modifier(ability_score) if isinstance(ability_score, int) else 0
    to_hit_bonus = attack.get("to_hit_bonus")
    if to_hit_bonus is None:
        to_hit_bonus = ability_mod + (proficiency_bonus if proficient else 0)

    return {
        "name": attack.get("name", "Attack"),
        "to_hit_bonus": to_hit_bonus,
        "damage_dice": damage_dice or "1d4",
        "damage_type": normalize_damage_type(str(damage_type) if damage_type is not None else None),
    }


def normalize_dnd5e_sheet_input(data: object) -> object:
    """Accept frontend nested sheet shape and normalize to backend flat schema."""
    if not isinstance(data, dict):
        return data

    abilities = data.get("abilities")
    if not isinstance(abilities, dict):
        abilities = {}

    proficiency_bonus = data.get("proficiency_bonus", 2)
    if isinstance(data.get("proficiency"), dict):
        proficiency = data["proficiency"]
        proficiency_bonus = proficiency.get("bonus", proficiency_bonus)
        skills = proficiency.get("skills", data.get("skills", []))
        saving_throws = proficiency.get("saving_throws", data.get("saving_throws", []))
    else:
        skills = data.get("skills", [])
        saving_throws = data.get("saving_throws", [])

    ac = data.get("ac", 10)
    hp = data.get("hp", {"max": 10, "current": 10, "temp": 0})
    hit_dice = data.get("hit_dice", "1d8")
    death_saves = data.get("death_saves", {"successes": 0, "failures": 0})
    initiative_modifier = data.get("initiative_modifier", 0)
    if isinstance(data.get("defense"), dict):
        defense = data["defense"]
        ac = defense.get("ac", ac)
        hp = defense.get("hp", hp)
        hit_dice = defense.get("hit_dice", hit_dice)
        death_saves = defense.get("death_saves", death_saves)
    if isinstance(data.get("initiative"), dict):
        initiative_modifier = data["initiative"].get("modifier", initiative_modifier)

    identity = normalize_sheet_identity(data.get("identity", {}))
    roleplay = data.get("roleplay", {})
    features_traits = data.get("features_traits", "")
    equipment = data.get("equipment", "")
    currency = data.get("currency", {})
    conditions = data.get("conditions", [])

    raw_attacks = data.get("attacks", [])
    attacks: list[dict[str, Any]] = []
    if isinstance(raw_attacks, list):
        for attack in raw_attacks:
            if isinstance(attack, dict):
                attacks.append(
                    _normalize_attack_entry(
                        attack,
                        abilities=abilities,
                        proficiency_bonus=proficiency_bonus if isinstance(proficiency_bonus, int) else 2,
                    )
                )

    return {
        "abilities": abilities,
        "proficiency_bonus": proficiency_bonus,
        "skills": skills,
        "saving_throws": saving_throws,
        "ac": ac,
        "hp": hp,
        "hit_dice": hit_dice,
        "death_saves": death_saves,
        "initiative_modifier": initiative_modifier,
        "identity": identity,
        "roleplay": roleplay,
        "features_traits": features_traits,
        "equipment": equipment,
        "currency": currency,
        "conditions": conditions,
        "attacks": attacks,
    }


class AttackEntry(BaseModel):
    name: str
    to_hit_bonus: int = 0
    damage_dice: str
    damage_type: str

    @field_validator("damage_type", mode="before")
    @classmethod
    def normalize_damage_type_field(cls, value: object) -> str:
        return normalize_damage_type(str(value) if value is not None else None)

    @model_validator(mode="before")
    @classmethod
    def normalize_frontend_attack(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        if "damage_dice" in data and "damage_type" in data:
            return {
                **data,
                "damage_type": normalize_damage_type(str(data.get("damage_type", ""))),
            }
        damage = data.get("damage")
        if isinstance(damage, dict):
            return {
                "name": data.get("name", "Attack"),
                "to_hit_bonus": data.get("to_hit_bonus", 0),
                "damage_dice": damage.get("dice", "1d4"),
                "damage_type": normalize_damage_type(str(damage.get("type", ""))),
            }
        return data

    @field_validator("damage_type")
    @classmethod
    def validate_damage_type(cls, value: str) -> str:
        if value not in DND5E_DAMAGE_TYPE_SLUGS:
            raise ValueError(f"Tipo de daño no válido: {value}")
        return value


class Dnd5eSheet(BaseModel):
    abilities: AbilityScores = Field(default_factory=AbilityScores)
    proficiency_bonus: int = Field(default=2, ge=0)
    skills: list[SkillEntry] = Field(default_factory=list)
    saving_throws: list[str] = Field(default_factory=list)
    ac: int = Field(default=10, ge=0)
    hp: HpBlock = Field(default_factory=HpBlock)
    hit_dice: str = ""
    death_saves: DeathSavesBlock = Field(default_factory=DeathSavesBlock)
    initiative_modifier: int = 0
    identity: SheetIdentityBlock = Field(default_factory=SheetIdentityBlock)
    roleplay: RoleplayBlock = Field(default_factory=RoleplayBlock)
    features_traits: str = ""
    equipment: str = ""
    currency: CurrencyBlock = Field(default_factory=CurrencyBlock)
    conditions: list[str] = Field(default_factory=list)
    attacks: list[AttackEntry] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_frontend_sheet(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        if "proficiency" in data or "defense" in data:
            return normalize_dnd5e_sheet_input(data)
        if isinstance(data.get("attacks"), list):
            attacks = data.get("attacks", [])
            abilities = data.get("abilities", {})
            if not isinstance(abilities, dict):
                abilities = {}
            prof_bonus = data.get("proficiency_bonus", 2)
            normalized_attacks = [
                _normalize_attack_entry(attack, abilities=abilities, proficiency_bonus=prof_bonus)
                for attack in attacks
                if isinstance(attack, dict)
            ]
            return {**data, "attacks": normalized_attacks}
        return data


ABILITY_LABELS_ES: dict[str, str] = {
    "str": "Fuerza",
    "dex": "Destreza",
    "con": "Constitución",
    "int": "Inteligencia",
    "wis": "Sabiduría",
    "cha": "Carisma",
}

SKILL_LABELS_ES: dict[str, str] = {
    "athletics": "Atletismo",
    "acrobatics": "Acrobacias",
    "sleight_of_hand": "Juego de manos",
    "stealth": "Sigilo",
    "arcana": "Arcano",
    "history": "Historia",
    "investigation": "Investigación",
    "nature": "Naturaleza",
    "religion": "Religión",
    "animal_handling": "Trato con animales",
    "insight": "Perspicacia",
    "medicine": "Medicina",
    "perception": "Percepción",
    "survival": "Supervivencia",
    "deception": "Engaño",
    "intimidation": "Intimidación",
    "performance": "Interpretación",
    "persuasion": "Persuasión",
}

ROLL_TYPE_LABELS_ES: dict[str, str] = {
    "ability_check": "Tirada de atributo",
    "saving_throw": "Salvación",
    "skill_check": "Tirada de habilidad",
    "attack_roll": "Ataque",
    "damage": "Daño",
    "initiative": "Iniciativa",
    "death_save": "Salvación contra la muerte",
}


def ability_label_es(ability: str) -> str:
    return ABILITY_LABELS_ES.get(ability.strip().lower(), ability)


def skill_label_es(skill: str) -> str:
    key = skill.strip().lower().replace(" ", "_")
    return SKILL_LABELS_ES.get(key, skill)


SKILL_ABILITY_MAP: dict[str, str] = {
    "athletics": "str",
    "acrobatics": "dex",
    "sleight_of_hand": "dex",
    "stealth": "dex",
    "arcana": "int",
    "history": "int",
    "investigation": "int",
    "nature": "int",
    "religion": "int",
    "animal_handling": "wis",
    "insight": "wis",
    "medicine": "wis",
    "perception": "wis",
    "survival": "wis",
    "deception": "cha",
    "intimidation": "cha",
    "performance": "cha",
    "persuasion": "cha",
}

SUPPORTED_ROLL_TYPES = [
    "ability_check",
    "saving_throw",
    "skill_check",
    "attack_roll",
    "damage",
    "initiative",
    "death_save",
]
