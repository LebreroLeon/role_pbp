import random
from copy import deepcopy

from pydantic import BaseModel

from app.rules.base import (
    DamageApplication,
    DamageResult,
    GameSystemPlugin,
    RollContext,
    RollResult,
)
from app.rules.vtm_v5.schema import (
    CATEGORY_DEFAULT_ATTRIBUTE,
    SUPPORTED_ROLL_TYPES,
    VTM_ATTRIBUTES,
    VtmV5Sheet,
)


def _normalize_key(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


def _parse_sheet(actor_sheet: dict) -> VtmV5Sheet:
    return VtmV5Sheet.model_validate(actor_sheet)


def _skill_entry(sheet: VtmV5Sheet, skill_name: str) -> tuple[str, int]:
    key = _normalize_key(skill_name)
    for entry in sheet.skills:
        if _normalize_key(entry.name) == key:
            category = _normalize_key(entry.category)
            attribute = CATEGORY_DEFAULT_ATTRIBUTE.get(category, "dex")
            return attribute, entry.dots
    raise ValueError(f"Unknown skill: {skill_name}")


def _discipline_entry(sheet: VtmV5Sheet, discipline_name: str) -> tuple[str, int]:
    key = _normalize_key(discipline_name)
    for entry in sheet.disciplines:
        if _normalize_key(entry.name) == key:
            return "wil", entry.level
    raise ValueError(f"Unknown discipline: {discipline_name}")


def _pool_expression(regular: int, hunger: int) -> str:
    if hunger:
        return f"{regular}d10+{hunger}d10h"
    return f"{regular}d10"


def _roll_vtm_pool(
    regular_size: int,
    hunger: int,
) -> tuple[list[int], list[int], int, list[int]]:
    regular_size = max(0, regular_size)
    hunger = max(0, min(hunger, 5))
    regular_rolls = [random.randint(1, 10) for _ in range(regular_size)]
    hunger_rolls = [random.randint(1, 10) for _ in range(hunger)]

    all_rolls = regular_rolls + hunger_rolls
    hunger_indices = list(range(len(regular_rolls), len(all_rolls)))

    successes = 0
    for idx, roll in enumerate(all_rolls):
        if roll >= 6:
            successes += 2 if roll == 10 else 1

    complications: list[int] = []
    for offset, roll in enumerate(hunger_rolls):
        if roll == 1:
            complications.append(hunger_indices[offset])

    return all_rolls, hunger_indices, successes, complications


class VtmV5Plugin(GameSystemPlugin):
    system_id = "vtm_v5"
    dice_mode = "dice_pool"
    sheet_schema_version = "1.0.0"

    def validate_pc_sheet(self, sheet: dict) -> BaseModel:
        return VtmV5Sheet.model_validate(sheet)

    def validate_npc_sheet(self, sheet: dict) -> BaseModel:
        return VtmV5Sheet.model_validate(sheet)

    def default_pc_sheet(self) -> dict:
        return VtmV5Sheet(
            attributes={
                "str": 2,
                "dex": 3,
                "sta": 2,
                "cha": 2,
                "man": 2,
                "com": 2,
                "int": 2,
                "wil": 3,
                "cer": 2,
            },
            skills=[
                {"name": "athletics", "category": "physical", "dots": 2},
                {"name": "stealth", "category": "physical", "dots": 1},
                {"name": "persuasion", "category": "social", "dots": 2},
                {"name": "investigation", "category": "mental", "dots": 1},
            ],
            disciplines=[{"name": "potence", "level": 1}],
            health={"superficial": 0, "aggravated": 0, "max": 7},
            hunger=1,
        ).model_dump()

    def default_npc_sheet(self, power_scale: str = "medium") -> dict:
        health_by_scale = {"weak": 5, "medium": 7, "strong": 9, "boss": 12}
        max_health = health_by_scale.get(power_scale, 7)
        return VtmV5Sheet(
            attributes={"str": 3, "dex": 2, "sta": 3, "wil": 2},
            skills=[{"name": "brawl", "category": "physical", "dots": 2}],
            health={"superficial": 0, "aggravated": 0, "max": max_health},
            hunger=0,
        ).model_dump()

    def resolve_roll(
        self,
        roll_type: str,
        actor_sheet: dict,
        context: RollContext,
    ) -> RollResult:
        sheet = _parse_sheet(actor_sheet)
        normalized = _normalize_key(roll_type)

        if normalized == "skill_check":
            return self._resolve_skill_check(sheet, context)
        if normalized == "attribute_check":
            return self._resolve_attribute_check(sheet, context)
        if normalized == "rouse_check":
            return self._resolve_rouse_check(sheet, context)
        if normalized == "discipline_check":
            return self._resolve_discipline_check(sheet, context)

        raise ValueError(
            f"Unsupported roll_type '{roll_type}' for vtm_v5. "
            f"Supported: {', '.join(SUPPORTED_ROLL_TYPES)}"
        )

    def _resolve_skill_check(self, sheet: VtmV5Sheet, context: RollContext) -> RollResult:
        if not context.skill:
            raise ValueError("skill_check requires context.skill")

        if context.ability:
            attribute = _normalize_key(context.ability)
            if attribute not in VTM_ATTRIBUTES:
                raise ValueError(f"Unknown attribute: {context.ability}")
            try:
                _, dots = _skill_entry(sheet, context.skill)
            except ValueError:
                dots = 0
        else:
            attribute, dots = _skill_entry(sheet, context.skill)

        pool = sheet.attributes.score(attribute) + dots
        if context.modifier_override is not None:
            pool = max(0, pool + context.modifier_override)
        return self._pool_roll(
            "skill_check",
            pool,
            sheet.hunger,
            context,
            attribute=attribute,
            skill=context.skill,
            skill_dots=dots,
        )

    def _resolve_attribute_check(self, sheet: VtmV5Sheet, context: RollContext) -> RollResult:
        if not context.ability:
            raise ValueError("attribute_check requires context.ability")
        attribute = _normalize_key(context.ability)
        pool = sheet.attributes.score(attribute)
        if context.modifier_override is not None:
            pool = max(0, pool + context.modifier_override)
        return self._pool_roll("attribute_check", pool, sheet.hunger, context, attribute=attribute)

    def _resolve_rouse_check(self, sheet: VtmV5Sheet, context: RollContext) -> RollResult:
        roll = random.randint(1, 10)
        success = roll >= 6
        hunger_after = min(5, sheet.hunger + (0 if success else 1))

        summary = f"Rouse check: d10({roll}) — {'éxito' if success else 'fallo'}"
        if not success:
            summary += f" (hambre {sheet.hunger} → {hunger_after})"

        return RollResult(
            roll_type="rouse_check",
            expression="1d10",
            rolls=[roll],
            total=roll,
            success=success,
            details={
                "hunger_before": sheet.hunger,
                "hunger_after": hunger_after,
                "rouse_failed": not success,
            },
            chat_summary=summary,
        )

    def _resolve_discipline_check(self, sheet: VtmV5Sheet, context: RollContext) -> RollResult:
        discipline_name = context.skill or context.attack_name
        if not discipline_name:
            raise ValueError("discipline_check requires context.skill or context.attack_name")

        if context.ability:
            attribute = _normalize_key(context.ability)
        else:
            attribute, _ = _discipline_entry(sheet, discipline_name)

        try:
            _, level = _discipline_entry(sheet, discipline_name)
        except ValueError:
            level = context.modifier_override or 0

        pool = sheet.attributes.score(attribute) + level
        return self._pool_roll(
            "discipline_check",
            pool,
            sheet.hunger,
            context,
            attribute=attribute,
            discipline=discipline_name,
            discipline_level=level,
        )

    def _pool_roll(
        self,
        roll_type: str,
        pool_size: int,
        hunger: int,
        context: RollContext,
        **extra_details: object,
    ) -> RollResult:
        hunger_dice = min(max(0, hunger), pool_size) if pool_size else 0
        regular_dice = max(0, pool_size - hunger_dice)
        rolls, hunger_indices, successes, complications = _roll_vtm_pool(regular_dice, hunger_dice)

        threshold = context.dc if context.dc is not None else 1
        success = successes >= threshold

        details: dict = {
            "pool_size": pool_size,
            "regular_dice": regular_dice,
            "hunger_dice": hunger_dice,
            "hunger": hunger,
            "successes": successes,
            "threshold": threshold,
            "hunger_dice_indices": hunger_indices,
            "hunger_complications": complications,
        }
        details.update(extra_details)
        if context.dc is not None:
            details["dc"] = context.dc

        label = roll_type.replace("_", " ")
        summary = f"{label}: {_pool_expression(regular_dice, hunger_dice)} → {successes} éxitos"
        if complications:
            summary += " (complicación de hambre)"
        if context.dc is not None:
            summary += f" vs dificultad {context.dc} — {'éxito' if success else 'fallo'}"

        return RollResult(
            roll_type=roll_type,
            expression=_pool_expression(regular_dice, hunger_dice),
            rolls=rolls,
            total=successes,
            success=success,
            details=details,
            chat_summary=summary,
        )

    def apply_damage(
        self,
        defender_sheet: dict,
        damage: DamageResult,
    ) -> tuple[dict, DamageApplication]:
        updated = deepcopy(defender_sheet)
        sheet = _parse_sheet(updated)
        hp_before = sheet.health.superficial + sheet.health.aggravated * 2
        sheet.health.superficial = min(sheet.health.max * 2, sheet.health.superficial + damage.amount)
        hp_after = sheet.health.superficial + sheet.health.aggravated * 2
        updated["health"] = sheet.health.model_dump()

        incapacitated = hp_after >= sheet.health.max * 2
        application = DamageApplication(
            damage_dealt=damage.amount,
            damage_type=damage.damage_type,
            hp_before=hp_before,
            hp_after=hp_after,
            is_unconscious=incapacitated,
            is_dead=False,
            chat_summary=(
                f"Daño {damage.amount} ({damage.damage_type}): "
                f"salud {hp_before} → {hp_after}"
            ),
        )
        return updated, application
