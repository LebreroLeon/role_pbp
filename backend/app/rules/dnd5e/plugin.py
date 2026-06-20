import random
import re
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
from app.rules.dnd5e.mechanics import apply_death_save_roll, passive_perception_from_sheet
from app.rules.dnd5e.rolls import roll_d20 as _roll_d20
from app.rules.dnd5e.schema import (
    Dnd5eSheet,
    SKILL_ABILITY_MAP,
    SUPPORTED_ROLL_TYPES,
    ability_label_es,
    skill_label_es,
)
from app.services import dice as dice_service


def ability_modifier(score: int) -> int:
    return (score - 10) // 2


def _normalize_key(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


def _parse_sheet(actor_sheet: dict) -> Dnd5eSheet:
    return Dnd5eSheet.model_validate(actor_sheet)


def _modifier_breakdown_entry(label: str, value: int) -> dict[str, int | str]:
    return {"label": label, "value": value}


def _skill_breakdown(sheet: Dnd5eSheet, skill_name: str) -> tuple[str, int, list[dict[str, int | str]]]:
    key = _normalize_key(skill_name)
    ability = SKILL_ABILITY_MAP.get(key)
    if ability is None:
        raise ValueError(f"Unknown skill: {skill_name}")

    ability_mod = ability_modifier(sheet.abilities.score(ability))
    breakdown: list[dict[str, int | str]] = [
        _modifier_breakdown_entry(ability_label_es(ability), ability_mod),
    ]
    proficiency_mod = 0
    expertise_mod = 0
    for entry in sheet.skills:
        if _normalize_key(entry.name) == key:
            if entry.proficient:
                proficiency_mod = sheet.proficiency_bonus
                breakdown.append(_modifier_breakdown_entry("Competencia", proficiency_mod))
            if entry.expertise:
                expertise_mod = sheet.proficiency_bonus
                breakdown.append(_modifier_breakdown_entry("Experiencia", expertise_mod))
            break

    total = ability_mod + proficiency_mod + expertise_mod
    return ability, total, breakdown


def _skill_entry(sheet: Dnd5eSheet, skill_name: str) -> tuple[str, int]:
    ability, total, _ = _skill_breakdown(sheet, skill_name)
    return ability, total


def _ability_check_modifier(sheet: Dnd5eSheet, ability: str) -> int:
    key = _normalize_key(ability)
    if key not in {"str", "dex", "con", "int", "wis", "cha"}:
        raise ValueError(f"Unknown ability: {ability}")
    return ability_modifier(sheet.abilities.score(key))


def _saving_throw_breakdown(
    sheet: Dnd5eSheet, ability: str
) -> tuple[int, list[dict[str, int | str]]]:
    ability_mod = _ability_check_modifier(sheet, ability)
    breakdown: list[dict[str, int | str]] = [
        _modifier_breakdown_entry(ability_label_es(ability), ability_mod),
    ]
    proficiency_mod = 0
    if _normalize_key(ability) in {_normalize_key(s) for s in sheet.saving_throws}:
        proficiency_mod = sheet.proficiency_bonus
        breakdown.append(_modifier_breakdown_entry("Competencia", proficiency_mod))
    return ability_mod + proficiency_mod, breakdown


def _saving_throw_modifier(sheet: Dnd5eSheet, ability: str) -> int:
    total, _ = _saving_throw_breakdown(sheet, ability)
    return total


def _attack_to_hit_breakdown(sheet: Dnd5eSheet, attack: object) -> list[dict[str, int | str]]:
    to_hit = getattr(attack, "to_hit_bonus", 0)
    if not isinstance(to_hit, int):
        to_hit = 0
    return [_modifier_breakdown_entry("Modificador de ataque", to_hit)]


def _format_dice_rolls(rolls: list[int], sides: int | None = None) -> str:
    if not rolls:
        return "?"
    if len(rolls) == 1:
        die = f"d{sides}" if sides else "d?"
        return f"1{die}={rolls[0]}"
    parts = [str(r) for r in rolls]
    return f"[{', '.join(parts)}]"


def _format_modifier_line(breakdown: list[dict[str, int | str]]) -> str:
    parts: list[str] = []
    for entry in breakdown:
        label = str(entry.get("label", ""))
        value = entry.get("value", 0)
        if not isinstance(value, int) or value == 0:
            continue
        sign = "+" if value > 0 else ""
        parts.append(f"{label} {sign}{value}")
    return ", ".join(parts)


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
                    "damage_type": "cortante",
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
                    "damage_type": "cortante",
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
        if normalized == "death_save":
            return self._resolve_death_save(sheet, context)

        raise ValueError(
            f"Unsupported roll_type '{roll_type}' for dnd5e. "
            f"Supported: {', '.join(SUPPORTED_ROLL_TYPES)}"
        )

    def _resolve_ability_check(self, sheet: Dnd5eSheet, context: RollContext) -> RollResult:
        if not context.ability:
            raise ValueError("ability_check requires context.ability")
        ability = _normalize_key(context.ability)
        modifier = context.modifier_override
        if modifier is None:
            modifier = _ability_check_modifier(sheet, context.ability)
        modifier_breakdown = [_modifier_breakdown_entry(ability_label_es(ability), modifier)]
        return self._d20_roll(
            "ability_check",
            modifier,
            context,
            roll_label=ability_label_es(ability),
            modifier_breakdown=modifier_breakdown,
            ability=ability,
        )

    def _resolve_saving_throw(self, sheet: Dnd5eSheet, context: RollContext) -> RollResult:
        if not context.ability:
            raise ValueError("saving_throw requires context.ability")
        ability = _normalize_key(context.ability)
        modifier = context.modifier_override
        modifier_breakdown: list[dict[str, int | str]] | None = None
        if modifier is None:
            modifier, modifier_breakdown = _saving_throw_breakdown(sheet, context.ability)
        else:
            modifier_breakdown = [_modifier_breakdown_entry(ability_label_es(ability), modifier)]
        return self._d20_roll(
            "saving_throw",
            modifier,
            context,
            roll_label=f"Salvación de {ability_label_es(ability)}",
            modifier_breakdown=modifier_breakdown,
            ability=ability,
        )

    def _resolve_skill_check(self, sheet: Dnd5eSheet, context: RollContext) -> RollResult:
        if not context.skill:
            raise ValueError("skill_check requires context.skill")
        ability, modifier, modifier_breakdown = _skill_breakdown(sheet, context.skill)
        if context.modifier_override is not None:
            modifier = context.modifier_override
        roll_label = f"{skill_label_es(context.skill)} ({ability_label_es(ability)})"
        return self._d20_roll(
            "skill_check",
            modifier,
            context,
            roll_label=roll_label,
            modifier_breakdown=modifier_breakdown,
            ability=ability,
            skill=context.skill,
        )

    def _resolve_attack_roll(self, sheet: Dnd5eSheet, context: RollContext) -> RollResult:
        idx, attack = _find_attack(sheet, context)
        modifier = context.modifier_override if context.modifier_override is not None else attack.to_hit_bonus
        modifier_breakdown = _attack_to_hit_breakdown(sheet, attack)
        result = self._d20_roll(
            "attack_roll",
            modifier,
            context,
            roll_label=attack.name,
            modifier_breakdown=modifier_breakdown,
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
            dice_label = self._d20_dice_label(context)
            mod_str = f"{modifier:+d}" if modifier else ""
            result.chat_summary = (
                f"{attack.name}: {dice_label}{mod_str} = {result.total} vs CA {context.target_ac} — "
                f"{'impacto' if hit else 'fallo'}"
            )
        else:
            dice_label = self._d20_dice_label(context)
            mod_str = f"{modifier:+d}" if modifier else ""
            result.chat_summary = f"{attack.name}: {dice_label}{mod_str} = {result.total}"
        return result

    def _resolve_damage(self, sheet: Dnd5eSheet, context: RollContext) -> RollResult:
        if context.expression:
            expression = context.expression
            damage_type = "sin tipo"
        else:
            _, attack = _find_attack(sheet, context)
            expression = attack.damage_dice
            damage_type = attack.damage_type

        raw = dice_service.roll_dice(expression)
        dice_total = raw["raw_result"]
        flat_modifier = raw["final_result"] - raw["raw_result"]
        rolls = raw["rolls"]
        total = raw["final_result"]

        dice_sides = None
        match = re.match(r"(\d+)d(\d+)", raw["dice_expression"])
        if match:
            dice_sides = int(match.group(2))

        modifier_breakdown: list[dict[str, int | str]] = []
        if rolls:
            dice_label = _format_dice_rolls(rolls, dice_sides)
            modifier_breakdown.append(
                {"label": dice_label, "value": dice_total, "rolls": rolls},
            )
        if flat_modifier:
            modifier_breakdown.append(_modifier_breakdown_entry("Modificador", flat_modifier))

        type_label = damage_type.replace("_", " ")
        roll_label = f"Daño ({type_label})"
        dice_part = _format_dice_rolls(rolls, dice_sides)
        summary = f"{roll_label}: {dice_part}"
        if flat_modifier:
            summary += f" {flat_modifier:+d}"
        summary += f" = {total}"

        return RollResult(
            roll_type="damage",
            expression=raw["dice_expression"],
            rolls=rolls,
            total=total,
            success=None,
            details={
                "roll_label": roll_label,
                "damage_type": damage_type,
                "raw_result": dice_total,
                "modifier": flat_modifier,
                "modifier_breakdown": modifier_breakdown,
                "dice_sides": dice_sides,
            },
            chat_summary=summary,
        )

    def _resolve_initiative(self, sheet: Dnd5eSheet, context: RollContext) -> RollResult:
        modifier = context.modifier_override
        if modifier is None:
            modifier = _ability_check_modifier(sheet, "dex") + sheet.initiative_modifier
        modifier_breakdown = [_modifier_breakdown_entry(ability_label_es("dex"), modifier)]
        return self._d20_roll(
            "initiative",
            modifier,
            context,
            roll_label="Iniciativa",
            modifier_breakdown=modifier_breakdown,
            ability="dex",
        )

    def _resolve_death_save(self, sheet: Dnd5eSheet, context: RollContext) -> RollResult:
        rolls, natural = _roll_d20(
            advantage=context.advantage,
            disadvantage=context.disadvantage,
        )
        applied = apply_death_save_roll(
            natural,
            sheet.death_saves.successes,
            sheet.death_saves.failures,
            sheet.hp.current,
        )

        passive = passive_perception_from_sheet(
            sheet.abilities.model_dump(),
            sheet.proficiency_bonus,
            [s.model_dump() for s in sheet.skills],
        )

        outcome_labels = {
            "success": "éxito",
            "failure": "fallo",
            "critical_success": "crítico — recuperas 1 PV",
            "critical_failure": "crítico — 2 fallos",
        }
        outcome_label = outcome_labels.get(applied["outcome"], applied["outcome"])
        summary = (
            f"Salvación contra la muerte: 1d20={natural} — {outcome_label}. "
            f"Éxitos {applied['successes']}/3, fallos {applied['failures']}/3"
        )
        if applied["stabilized"]:
            summary += " — estabilizado"
        if applied["dead"]:
            summary += " — muerto"

        return RollResult(
            roll_type="death_save",
            expression="1d20",
            rolls=rolls,
            total=natural,
            success=applied["is_success"],
            details={
                "roll_label": "Salvación contra la muerte",
                "natural_roll": natural,
                "modifier": 0,
                "modifier_breakdown": [],
                "death_save_successes": applied["successes"],
                "death_save_failures": applied["failures"],
                "hp_current": applied["hp_current"],
                "stabilized": applied["stabilized"],
                "dead": applied["dead"],
                "outcome": applied["outcome"],
                "passive_perception": passive,
            },
            chat_summary=summary,
        )

    @staticmethod
    def _d20_dice_label(context: RollContext) -> str:
        if context.advantage:
            return "2d20 (ventaja)"
        if context.disadvantage:
            return "2d20 (desventaja)"
        return "1d20"

    def _d20_roll(
        self,
        roll_type: str,
        modifier: int,
        context: RollContext,
        *,
        roll_label: str | None = None,
        modifier_breakdown: list[dict[str, int | str]] | None = None,
        **extra_details: object,
    ) -> RollResult:
        rolls, natural = _roll_d20(advantage=context.advantage, disadvantage=context.disadvantage)
        total = natural + modifier
        success = None
        if context.dc is not None:
            success = total >= context.dc

        sign = f"{modifier:+d}" if modifier else ""
        dice_label = self._d20_dice_label(context)
        expr = f"{dice_label}{sign}"

        details: dict = {
            "natural_roll": natural,
            "modifier": modifier,
            "advantage": context.advantage,
            "disadvantage": context.disadvantage,
            "modifier_breakdown": modifier_breakdown or [],
        }
        if roll_label:
            details["roll_label"] = roll_label
        if context.dc is not None:
            details["dc"] = context.dc
        details.update(extra_details)

        label = roll_label or roll_type.replace("_", " ")
        summary = f"{label}: {dice_label}={natural}"
        if modifier:
            summary += f" {sign}"
        summary += f" = {total}"
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
                modifier=int(damage_roll.details.get("modifier", 0)),
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
