from pydantic import BaseModel, ConfigDict, Field

VTM_ATTRIBUTES = (
    "str",
    "dex",
    "sta",
    "cha",
    "man",
    "com",
    "int",
    "wil",
    "cer",
)

VTM_SKILL_CATEGORIES = ("physical", "social", "mental")

CATEGORY_DEFAULT_ATTRIBUTE: dict[str, str] = {
    "physical": "dex",
    "social": "man",
    "mental": "int",
}


class AttributeBlock(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    str: int = Field(default=1, ge=1, le=5)
    dex: int = Field(default=1, ge=1, le=5)
    sta: int = Field(default=1, ge=1, le=5)
    cha: int = Field(default=1, ge=1, le=5)
    man: int = Field(default=1, ge=1, le=5)
    com: int = Field(default=1, ge=1, le=5)
    intelligence: int = Field(default=1, ge=1, le=5, validation_alias="int", serialization_alias="int")
    wil: int = Field(default=1, ge=1, le=5)
    cer: int = Field(default=1, ge=1, le=5)

    def score(self, attribute: str) -> int:
        key = attribute.strip().lower()
        if key not in VTM_ATTRIBUTES:
            raise ValueError(f"Unknown attribute: {attribute}")
        if key == "int":
            return self.intelligence
        return getattr(self, key)


class SkillEntry(BaseModel):
    name: str
    category: str = "physical"
    dots: int = Field(default=0, ge=0, le=5)


class DisciplineEntry(BaseModel):
    name: str
    level: int = Field(default=1, ge=1, le=5)


class HealthBlock(BaseModel):
    superficial: int = Field(default=0, ge=0)
    aggravated: int = Field(default=0, ge=0)
    max: int = Field(default=7, ge=1)


class VtmV5Sheet(BaseModel):
    attributes: AttributeBlock = Field(default_factory=AttributeBlock)
    skills: list[SkillEntry] = Field(default_factory=list)
    disciplines: list[DisciplineEntry] = Field(default_factory=list)
    health: HealthBlock = Field(default_factory=HealthBlock)
    hunger: int = Field(default=1, ge=0, le=5)


SUPPORTED_ROLL_TYPES = [
    "skill_check",
    "attribute_check",
    "rouse_check",
    "discipline_check",
]
