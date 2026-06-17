from pydantic import BaseModel, ConfigDict, Field


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


class AttackEntry(BaseModel):
    name: str
    to_hit_bonus: int = 0
    damage_dice: str
    damage_type: str


class Dnd5eSheet(BaseModel):
    abilities: AbilityScores = Field(default_factory=AbilityScores)
    proficiency_bonus: int = Field(default=2, ge=0)
    skills: list[SkillEntry] = Field(default_factory=list)
    saving_throws: list[str] = Field(default_factory=list)
    ac: int = Field(default=10, ge=0)
    hp: HpBlock = Field(default_factory=HpBlock)
    attacks: list[AttackEntry] = Field(default_factory=list)


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
]
