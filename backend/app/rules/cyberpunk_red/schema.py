from pydantic import BaseModel, ConfigDict, Field

CYBERPUNK_STATS = (
    "int",
    "ref",
    "tech",
    "cool",
    "attr",
    "luck",
    "move",
    "body",
    "emp",
)


class StatBlock(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    intelligence: int = Field(default=4, ge=1, le=10, validation_alias="int", serialization_alias="int")
    ref: int = Field(default=4, ge=1, le=10)
    tech: int = Field(default=4, ge=1, le=10)
    cool: int = Field(default=4, ge=1, le=10)
    attr: int = Field(default=4, ge=1, le=10)
    luck: int = Field(default=4, ge=1, le=10)
    move: int = Field(default=4, ge=1, le=10)
    body: int = Field(default=4, ge=1, le=10)
    emp: int = Field(default=4, ge=1, le=10)

    def score(self, stat: str) -> int:
        key = stat.strip().lower()
        if key not in CYBERPUNK_STATS:
            raise ValueError(f"Unknown stat: {stat}")
        if key == "int":
            return self.intelligence
        return getattr(self, key)


class SkillEntry(BaseModel):
    name: str
    stat: str = "ref"
    rank: int = Field(default=0, ge=0, le=10)


class HpBlock(BaseModel):
    max: int = Field(default=40, ge=1)
    current: int = Field(default=40, ge=0)


class ArmorBlock(BaseModel):
    head: int = Field(default=0, ge=0, le=25)
    body: int = Field(default=0, ge=0, le=25)


class WeaponEntry(BaseModel):
    name: str
    stat: str = "ref"
    skill: str = "handgun"
    damage_dice: str = "2d6"
    damage_type: str = "ballistic"


class CyberpunkRedSheet(BaseModel):
    stats: StatBlock = Field(default_factory=StatBlock)
    skills: list[SkillEntry] = Field(default_factory=list)
    hp: HpBlock = Field(default_factory=HpBlock)
    armor: ArmorBlock = Field(default_factory=ArmorBlock)
    weapons: list[WeaponEntry] = Field(default_factory=list)


SUPPORTED_ROLL_TYPES = [
    "skill_check",
    "stat_check",
    "attack_roll",
    "damage",
    "initiative",
]
