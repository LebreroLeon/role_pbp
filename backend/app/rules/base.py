from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel

DiceMode = Literal["d20", "dice_pool", "d100", "generic"]


@dataclass
class RollContext:
    ability: str | None = None
    skill: str | None = None
    attack_name: str | None = None
    attack_index: int | None = None
    dc: int | None = None
    target_ac: int | None = None
    advantage: bool = False
    disadvantage: bool = False
    modifier_override: int | None = None
    expression: str | None = None


@dataclass
class RollResult:
    roll_type: str
    expression: str
    rolls: list[int]
    total: int | None
    success: bool | None
    details: dict[str, Any] = field(default_factory=dict)
    chat_summary: str = ""


@dataclass
class AttackContext:
    advantage: bool = False
    disadvantage: bool = False
    target_ac: int | None = None
    attack_name: str | None = None
    attack_index: int | None = None


@dataclass
class DamageResult:
    amount: int
    expression: str
    rolls: list[int]
    damage_type: str
    modifier: int = 0
    is_healing: bool = False


@dataclass
class AttackResult:
    attack_roll: RollResult
    hit: bool
    damage: DamageResult | None
    chat_summary: str


@dataclass
class DamageApplication:
    damage_dealt: int
    damage_type: str
    hp_before: int
    hp_after: int
    is_unconscious: bool = False
    is_dead: bool = False
    is_healing: bool = False
    amount_applied: int | None = None
    chat_summary: str = ""


class GameSystemPlugin(ABC):
    system_id: str
    dice_mode: DiceMode
    sheet_schema_version: str

    @abstractmethod
    def validate_pc_sheet(self, sheet: dict) -> BaseModel: ...

    @abstractmethod
    def validate_npc_sheet(self, sheet: dict) -> BaseModel: ...

    @abstractmethod
    def default_pc_sheet(self) -> dict: ...

    @abstractmethod
    def default_npc_sheet(self, power_scale: str = "medium") -> dict: ...

    @abstractmethod
    def resolve_roll(
        self,
        roll_type: str,
        actor_sheet: dict,
        context: RollContext,
    ) -> RollResult: ...

    def resolve_attack(
        self,
        attacker_sheet: dict,
        defender_sheet: dict,
        weapon_or_attack_id: str | None,
        context: AttackContext,
    ) -> AttackResult:
        raise NotImplementedError(f"{self.system_id} does not support resolve_attack yet")

    def apply_damage(
        self,
        defender_sheet: dict,
        damage: DamageResult,
    ) -> tuple[dict, DamageApplication]:
        raise NotImplementedError(f"{self.system_id} does not support apply_damage yet")
