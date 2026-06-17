import random
from copy import deepcopy

from pydantic import BaseModel

from app.rules.base import (
    AttackContext,
    AttackResult,
    DamageApplication,
    DamageResult,
    GameSystemPlugin,
    RollContext,
    RollResult,
)
from app.rules.dnd5e.schema import (
    Dnd5eSheet,
    SKILL_ABILITY_MAP,
    SUPPORTED_ROLL_TYPES,
)
from app.services import dice as dice_service


def ability_modifier(score: int) -> int:
    return (score - 10) // 2


def _normalize_key(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


def _roll_d20(advantage: bool = False, disadvantage: bool = False) -> tuple[list[int], int]:
    if advantage and disadvantage:
        advantage = False
        disadvantage = False

    if advantage or disadvantage:
        rolls = [random.randint(1, 20), random.randint(1, 20)]
        chosen = max(rolls) if advantage else min(rolls)
        return rolls, chosen

    roll = random.randint(1, 20)
    return [roll], roll


def _parse_sheet(actor_sheet: dict) -> Dnd5eSheet:
    return Dnd5eSheet.model_validate(actor_sheet)


def _skill_entry(sheet: Dnd5eSheet, skill_name: str) -> tuple[str, int]:
    key = _normalize_key(skill_name)
    ability = SKILL_ABILITY_MAP.get(key)
    if ability is None:
        raise ValueError(f"Unknown skill: {skill_name}")

    ability_mod = ability_modifier(sheet.abilities.score(ability))
    bonus = 0
    for entry in sheet.skills:
        if _normalize_key(entry.name) == key:
            if entry.proficient:
                bonus += sheet.proficiency_bonus
            if entry.expertise:
                bonus += sheet.proficiency_bonus
            break

    return ability, ability_mod + bonus


def _ability_check_modifier(sheet: Dnd5eSheet, ability: str) -> int:
    key = _normalize_key(ability)
    if key not in {"str", "dex", "con", "int", "wis", "cha"}:
        raise ValueError(f"Unknown ability: {ability}")
    return ability_modifier(sheet.abilities.score(key))


def _saving_throw_modifier(sheet: Dnd5eSheet, ability: str) -> int:
    mod = _ability_check_modifier(sheet, ability)
    if _normalize_key(ability) in {_normalize_key(s) for s in sheet.saving_throws}:
        mod += sheet.proficiency_bonus
    return mod


def _find_attack(sheet: Dnd5eSheet, context: RollContext | AttackContext) -> tuple[int, object]:
    if context.attack_index is not None:
        idx = context.attack_index
        if idx < 0 or idx >= len(sheet.attacks):
            raise ValueError(f"Attack index out of range: {idx}")
        return idx, sheet.attacks[idx]

    if context.attack_name:
        key = _normalize_key(context.attack_name)
        for idx, attack in enumerate(sheet.attacks):
            if _normalize_key(attack.name) == key:
                return idx, attack
        raise ValueError(f"Attack not found: {context.attack_name}")

    if sheet.attacks:
        return 0, sheet.attacks[0]

    raise ValueError("No attacks defined on sheet")


class Dnd5ePlugin(GameSystemPlugin):
    system_id = "dnd5e"
    dice_mode = "d20"
    sheet_schema_version = "1.0.0"

    def validate_pc_sheet(self, sheet: dict) -> BaseModel:
        return Dnd5eSheet.model_validate(sheet)

    def validate_npc_sheet(self, sheet: dict) -> BaseModel:
        return Dnd5eSheet.model_validate(sheet)

    def default_pc_sheet(self) -> dict:
        return Dnd5eSheet(
            abilities={"str": 14, "dex": 12, "con": 13, "int": 10, "wis": 11, "cha": 8},
            proficiency_bonus=2,
            skills=[
                {"name": "perception", "proficient": True},
                {"name": "athletics", "proficient": True},
            ],
            saving_throws=["dex", "wis"],
            ac=15,
            hp={"max": 24, "current": 24},
            attacks=[
                {
                    "name": "Longsword",
                    "to_hit_bonus": 5,
                    "damage_dice": "1d8+3",
                    "damage_type": "slashing",
                }
            ],
        ).model_dump()

    def default_npc_sheet(self, power_scale: str = "medium") -> dict:
        hp_by_scale = {"weak": 8, "medium": 16, "strong": 32, "boss": 64}
        max_hp = hp_by_scale.get(power_scale, 16)
        return Dnd5eSheet(
            ac=12,
            hp={"max": max_hp, "current": max_hp},
            attacks=[
                {
                    "name": "Claw",
                    "to_hit_bonus": 4,
                    "damage_dice": "1d6+2",
                    "damage_type": "slashing",
                }
            ],
        ).model_dump()

    def resolve_roll(
        self,
        roll_type: str,
        actor_sheet: dict,
        context: RollContext,
    ) -> RollResult:
        sheet = _parse_sheet(actor_sheet)
        normalized = _normalize_key(roll_type)

        if normalized == "ability_check":
            return self._resolve_ability_check(sheet, context)
        if normalized == "saving_throw":
            return self._resolve_saving_throw(sheet, context)
        if normalized == "skill_check":
            return self._resolve_skill_check(sheet, context)
        if normalized in {"attack_roll", "attack"}:
            return self._resolve_attack_roll(sheet, context)
        if normalized == "damage":
            return self._resolve_damage(sheet, context)
        if normalized == "initiative":
            return self._resolve_initiative(sheet, context)

        raise ValueError(
            f"Unsupported roll_type '{roll_type}' for dnd5e. "
            f"Supported: {', '.join(SUPPORTED_ROLL_TYPES)}"
        )

    def _resolve_ability_check(self, sheet: Dnd5eSheet, context: RollContext) -> RollResult:
        if not context.ability:
            raise ValueError("ability_check requires context.ability")
        modifier = context.modifier_override
        if modifier is None:
            modifier = _ability_check_modifier(sheet, context.ability)
        return self._d20_roll("ability_check", modifier, context, ability=context.ability)

    def _resolve_saving_throw(self, sheet: Dnd5eSheet, context: RollContext) -> RollResult:
        if not context.ability:
            raise ValueError("saving_throw requires context.ability")
        modifier = context.modifier_override
        if modifier is None:
            modifier = _saving_throw_modifier(sheet, context.ability)
        return self._d20_roll("saving_throw", modifier, context, ability=context.ability)

    def _resolve_skill_check(self, sheet: Dnd5eSheet, context: RollContext) -> RollResult:
        if not context.skill:
            raise ValueError("skill_check requires context.skill")
        ability, modifier = _skill_entry(sheet, context.skill)
        if context.modifier_override is not None:
            modifier = context.modifier_override
        return self._d20_roll(
            "skill_check",
            modifier,
            context,
            ability=ability,
            skill=context.skill,
        )

    def _resolve_attack_roll(self, sheet: Dnd5eSheet, context: RollContext) -> RollResult:
        idx, attack = _find_attack(sheet, context)
        modifier = context.modifier_override if context.modifier_override is not None else attack.to_hit_bonus
        result = self._d20_roll(
            "attack_roll",
            modifier,
            context,
            attack_name=attack.name,
            attack_index=idx,
            damage_dice=attack.damage_dice,
            damage_type=attack.damage_type,
        )
        if context.target_ac is not None and result.total is not None:
            natural = result.rolls[-1] if result.rolls else None
            hit = natural == 20 or (natural != 1 and result.total >= context.target_ac)
            result.success = hit
            result.details["target_ac"] = context.target_ac
            result.details["hit"] = hit
            result.chat_summary = (
                f"Ataque ({attack.name}): {result.total} vs CA {context.target_ac} — "
                f"{'impacto' if hit else 'fallo'}"
            )
        else:
            result.chat_summary = f"Ataque ({attack.name}): 1d20{modifier:+d} = {result.total}"
        return result

    def _resolve_damage(self, sheet: Dnd5eSheet, context: RollContext) -> RollResult:
        if context.expression:
            expression = context.expression
            damage_type = "untyped"
        else:
            _, attack = _find_attack(sheet, context)
            expression = attack.damage_dice
            damage_type = attack.damage_type

        raw = dice_service.roll_dice(expression)
        total = raw["final_result"]
        return RollResult(
            roll_type="damage",
            expression=raw["dice_expression"],
            rolls=raw["rolls"],
            total=total,
            success=None,
            details={
                "damage_type": damage_type,
                "raw_result": raw["raw_result"],
                "modifier": raw["final_result"] - raw["raw_result"],
            },
            chat_summary=f"Daño ({damage_type}): {expression} = {total}",
        )

    def _resolve_initiative(self, sheet: Dnd5eSheet, context: RollContext) -> RollResult:
        modifier = context.modifier_override
        if modifier is None:
            modifier = _ability_check_modifier(sheet, "dex")
        return self._d20_roll("initiative", modifier, context, ability="dex")

    def _d20_roll(
        self,
        roll_type: str,
        modifier: int,
        context: RollContext,
        **extra_details: object,
    ) -> RollResult:
        rolls, natural = _roll_d20(context.advantage, context.disadvantage)
        total = natural + modifier
        success = None
        if context.dc is not None:
            success = total >= context.dc

        sign = f"{modifier:+d}" if modifier else ""
        expr = f"1d20{sign}"
        if context.advantage:
            expr = f"2d20adv{sign}"
        elif context.disadvantage:
            expr = f"2d20dis{sign}"

        details: dict = {
            "natural_roll": natural,
            "modifier": modifier,
            "advantage": context.advantage,
            "disadvantage": context.disadvantage,
        }
        if context.dc is not None:
            details["dc"] = context.dc
        details.update(extra_details)

        label = roll_type.replace("_", " ")
        summary = f"{label}: {natural}{sign} = {total}"
        if context.dc is not None:
            summary += f" vs CD {context.dc} — {'éxito' if success else 'fallo'}"

        return RollResult(
            roll_type=roll_type,
            expression=expr,
            rolls=rolls,
            total=total,
            success=success,
            details=details,
            chat_summary=summary,
        )

    def resolve_attack(
        self,
        attacker_sheet: dict,
        defender_sheet: dict,
        weapon_or_attack_id: str | None,
        context: AttackContext,
    ) -> AttackResult:
        defender = _parse_sheet(defender_sheet)
        target_ac = context.target_ac if context.target_ac is not None else defender.ac

        roll_ctx = RollContext(
            attack_name=weapon_or_attack_id or context.attack_name,
            attack_index=context.attack_index,
            target_ac=target_ac,
            advantage=context.advantage,
            disadvantage=context.disadvantage,
        )
        attack_roll = self.resolve_roll("attack_roll", attacker_sheet, roll_ctx)
        hit = bool(attack_roll.details.get("hit", attack_roll.success))

        damage_result = None
        if hit:
            damage_roll = self.resolve_roll(
                "damage",
                attacker_sheet,
                RollContext(
                    attack_name=weapon_or_attack_id or context.attack_name,
                    attack_index=context.attack_index,
                ),
            )
            damage_type = str(damage_roll.details.get("damage_type", "untyped"))
            damage_result = DamageResult(
                amount=damage_roll.total or 0,
                expression=damage_roll.expression,
                rolls=damage_roll.rolls,
                damage_type=damage_type,
            )

        attacker_name = weapon_or_attack_id or context.attack_name or "ataque"
        if hit and damage_result:
            summary = (
                f"{attacker_name}: {attack_roll.total} vs CA {target_ac} — impacto. "
                f"{damage_result.amount} {damage_result.damage_type}."
            )
        else:
            summary = f"{attacker_name}: {attack_roll.total} vs CA {target_ac} — fallo."

        return AttackResult(
            attack_roll=attack_roll,
            hit=hit,
            damage=damage_result,
            chat_summary=summary,
        )

    def apply_damage(
        self,
        defender_sheet: dict,
        damage: DamageResult,
    ) -> tuple[dict, DamageApplication]:
        updated = deepcopy(defender_sheet)
        sheet = _parse_sheet(updated)
        hp_before = sheet.hp.current
        sheet.hp.current = max(0, sheet.hp.current - damage.amount)
        updated["hp"] = sheet.hp.model_dump()

        application = DamageApplication(
            damage_dealt=damage.amount,
            damage_type=damage.damage_type,
            hp_before=hp_before,
            hp_after=sheet.hp.current,
            is_unconscious=sheet.hp.current == 0,
            is_dead=False,
            chat_summary=(
                f"Daño {damage.amount} ({damage.damage_type}): "
                f"PV {hp_before} → {sheet.hp.current}"
            ),
        )
        return updated, application
