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
from app.rules.dnd5e.damage_types import normalize_damage_type
from app.rules.dnd5e.mechanics import (
    apply_damage_pipeline,
    apply_death_save_roll,
    double_damage_dice,
    has_meaningful_damage_dice,
    passive_perception_from_sheet,
)
from app.rules.dnd5e.save_attack_format import damage_type_label_es, format_save_damage_taken_line
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


def _spell_save_dc(sheet: Dnd5eSheet) -> int:
    if sheet.spellcasting.save_dc is not None:
        return sheet.spellcasting.save_dc
    ability = _normalize_key(sheet.spellcasting.ability)
    if ability not in {"str", "dex", "con", "int", "wis", "cha"}:
        ability = "int"
    return 8 + sheet.proficiency_bonus + ability_modifier(sheet.abilities.score(ability))


def _attack_save_ability(attack: object) -> str:
    save_ability = getattr(attack, "save_ability", None)
    if isinstance(save_ability, str) and save_ability.strip():
        return _normalize_key(save_ability)
    return "dex"


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
        if normalized in {"damage", "healing"}:
            return self._resolve_damage(sheet, context, healing=normalized == "healing")
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
            is_critical = natural == 20
            hit = is_critical or (natural != 1 and result.total >= context.target_ac)
            result.success = hit
            result.details["target_ac"] = context.target_ac
            result.details["hit"] = hit
            result.details["is_critical"] = is_critical
            dice_label = self._d20_dice_label(context)
            mod_str = f"{modifier:+d}" if modifier else ""
            hit_label = "impacto crítico" if is_critical and hit else ("impacto" if hit else "fallo")
            result.chat_summary = (
                f"{attack.name}: {dice_label}{mod_str} = {result.total} vs CA {context.target_ac} — "
                f"{hit_label}"
            )
        else:
            dice_label = self._d20_dice_label(context)
            mod_str = f"{modifier:+d}" if modifier else ""
            result.chat_summary = f"{attack.name}: {dice_label}{mod_str} = {result.total}"
        return result

    def _resolve_damage(
        self,
        sheet: Dnd5eSheet,
        context: RollContext,
        *,
        healing: bool = False,
    ) -> RollResult:
        if context.expression:
            expression = context.expression
            damage_type = ""
            is_healing = healing
        else:
            _, attack = _find_attack(sheet, context)
            expression = attack.damage_dice
            damage_type = attack.damage_type
            is_healing = attack.effect_type == "healing" or healing

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

        type_label = damage_type_label_es(damage_type) or "daño"
        effect_label = "Curación" if is_healing else "Daño"
        roll_label = f"{effect_label} ({type_label})" if type_label != "daño" or is_healing else "Daño"
        dice_part = _format_dice_rolls(rolls, dice_sides)
        summary = f"{roll_label}: {dice_part}"
        if flat_modifier:
            summary += f" {flat_modifier:+d}"
        summary += f" = {total}"

        roll_type = "healing" if is_healing else "damage"

        return RollResult(
            roll_type=roll_type,
            expression=raw["dice_expression"],
            rolls=rolls,
            total=total,
            success=None,
            details={
                "roll_label": roll_label,
                "damage_type": damage_type,
                "effect_type": "healing" if is_healing else "damage",
                "is_healing": is_healing,
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
        attacker = _parse_sheet(attacker_sheet)
        defender = _parse_sheet(defender_sheet)
        target_ac = context.target_ac if context.target_ac is not None else defender.ac

        _, attack = _find_attack(
            attacker,
            AttackContext(
                attack_name=weapon_or_attack_id or context.attack_name,
                attack_index=context.attack_index,
            ),
        )
        is_healing = attack.effect_type == "healing"
        attacker_name = weapon_or_attack_id or context.attack_name or attack.name or "ataque"

        if is_healing:
            damage_roll = self.resolve_roll(
                "healing",
                attacker_sheet,
                RollContext(
                    attack_name=weapon_or_attack_id or context.attack_name,
                    attack_index=context.attack_index,
                ),
            )
            damage_result = DamageResult(
                amount=damage_roll.total or 0,
                expression=damage_roll.expression,
                rolls=damage_roll.rolls,
                damage_type=str(damage_roll.details.get("damage_type", "radiante")),
                modifier=int(damage_roll.details.get("modifier", 0)),
                is_healing=True,
            )
            placeholder_roll = RollResult(
                roll_type="healing",
                expression="—",
                rolls=[],
                total=None,
                success=True,
                details={
                    "roll_label": attack.name,
                    "healing": True,
                    "attack_name": attack.name,
                },
                chat_summary=f"{attack.name}: curación",
            )
            summary = (
                f"{attacker_name} cura: {damage_result.amount} "
                f"{damage_result.damage_type.replace('_', ' ')}."
            )
            return AttackResult(
                attack_roll=placeholder_roll,
                hit=True,
                damage=damage_result,
                chat_summary=summary,
            )

        if getattr(attack, "resolution", "attack_roll") == "save":
            return self._resolve_save_attack(
                attacker,
                attacker_sheet,
                defender_sheet,
                attack,
                context,
                weapon_or_attack_id=weapon_or_attack_id,
                attacker_name=attacker_name,
            )

        roll_ctx = RollContext(
            attack_name=weapon_or_attack_id or context.attack_name,
            attack_index=context.attack_index,
            target_ac=target_ac,
            advantage=context.advantage,
            disadvantage=context.disadvantage,
        )
        attack_roll = self.resolve_roll("attack_roll", attacker_sheet, roll_ctx)
        hit = bool(attack_roll.details.get("hit", attack_roll.success))
        is_critical = bool(attack_roll.details.get("is_critical"))

        damage_result = None
        if hit:
            damage_ctx = RollContext(
                attack_name=weapon_or_attack_id or context.attack_name,
                attack_index=context.attack_index,
            )
            if is_critical:
                damage_ctx.expression = double_damage_dice(attack.damage_dice)
            damage_roll = self.resolve_roll("damage", attacker_sheet, damage_ctx)
            damage_type = normalize_damage_type(
                str(damage_roll.details.get("damage_type", "") or getattr(attack, "damage_type", "") or ""),
                default="",
            )
            damage_result = DamageResult(
                amount=damage_roll.total or 0,
                expression=damage_roll.expression,
                rolls=damage_roll.rolls,
                damage_type=damage_type,
                modifier=int(damage_roll.details.get("modifier", 0)),
                is_healing=False,
                is_critical=is_critical,
            )

        if hit and damage_result:
            crit_note = " (crítico)" if is_critical else ""
            summary = (
                f"{attacker_name}: {attack_roll.total} vs CA {target_ac} — impacto{crit_note}. "
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

    def _resolve_save_attack(
        self,
        attacker: Dnd5eSheet,
        attacker_sheet: dict,
        defender_sheet: dict,
        attack: object,
        context: AttackContext,
        *,
        weapon_or_attack_id: str | None,
        attacker_name: str,
    ) -> AttackResult:
        save_ability = _attack_save_ability(attack)
        spell_dc = _spell_save_dc(attacker)
        half_on_save = bool(getattr(attack, "half_damage_on_save", False))
        attack_name = getattr(attack, "name", None) or weapon_or_attack_id or attacker_name

        save_roll = self.resolve_roll(
            "saving_throw",
            defender_sheet,
            RollContext(
                ability=save_ability,
                dc=spell_dc,
                advantage=context.advantage,
                disadvantage=context.disadvantage,
            ),
        )
        save_succeeded = bool(save_roll.success)
        spell_affects = not save_succeeded

        save_roll.details["save_dc"] = spell_dc
        save_roll.details["save_ability"] = save_ability
        save_roll.details["save_succeeded"] = save_succeeded
        save_roll.details["resolution"] = "save"
        save_roll.details["half_damage_on_save"] = half_on_save
        save_roll.details["attack_name"] = attack_name
        save_roll.details["hit"] = spell_affects

        ability_label = ability_label_es(save_ability)
        save_roll.chat_summary = (
            f"Salvación de {ability_label}: {save_roll.total} vs CD {spell_dc} — "
            f"{'superada' if save_succeeded else 'fallida'}"
        )

        damage_result = None
        damage_dice = str(getattr(attack, "damage_dice", "") or "")
        if has_meaningful_damage_dice(damage_dice) and attack.effect_type == "damage":
            should_apply_damage = spell_affects or (save_succeeded and half_on_save)
            if should_apply_damage:
                damage_ctx = RollContext(
                    attack_name=weapon_or_attack_id or context.attack_name,
                    attack_index=context.attack_index,
                    expression=damage_dice,
                )
                damage_roll = self.resolve_roll("damage", attacker_sheet, damage_ctx)
                amount = damage_roll.total or 0
                if save_succeeded and half_on_save:
                    amount = amount // 2
                damage_type = normalize_damage_type(
                    str(getattr(attack, "damage_type", "") or damage_roll.details.get("damage_type", "") or ""),
                    default="",
                )
                damage_result = DamageResult(
                    amount=amount,
                    expression=damage_roll.expression,
                    rolls=damage_roll.rolls,
                    damage_type=damage_type,
                    modifier=int(damage_roll.details.get("modifier", 0)),
                    is_healing=False,
                    is_critical=False,
                )
                save_roll.details["damage_roll_summary"] = damage_roll.chat_summary

        if damage_result is not None:
            damage_line = format_save_damage_taken_line(
                defender_name="el objetivo",
                amount=damage_result.amount,
                damage_type=damage_result.damage_type,
            )
            if save_succeeded and half_on_save:
                summary = (
                    f"{attacker_name}: CD {spell_dc} — salvación superada, mitad de daño. {damage_line}."
                )
            else:
                summary = f"{attacker_name}: CD {spell_dc} — salvación fallida. {damage_line}."
        elif save_succeeded:
            summary = f"{attacker_name}: CD {spell_dc} — salvación superada, el hechizo no afecta."
        else:
            summary = f"{attacker_name}: CD {spell_dc} — salvación fallida, el objetivo queda afectado."

        return AttackResult(
            attack_roll=save_roll,
            hit=spell_affects or damage_result is not None,
            damage=damage_result,
            chat_summary=summary,
        )

    def apply_damage(
        self,
        defender_sheet: dict,
        damage: DamageResult,
    ) -> tuple[dict, DamageApplication]:
        if damage.is_healing:
            updated = deepcopy(defender_sheet)
            sheet = _parse_sheet(updated)
            hp_before = sheet.hp.current
            applied = min(damage.amount, max(0, sheet.hp.max - sheet.hp.current))
            sheet.hp.current = hp_before + applied
            if isinstance(updated.get("defense"), dict):
                updated["defense"]["hp"] = sheet.hp.model_dump()
            updated["hp"] = sheet.hp.model_dump()

            if sheet.hp.current > 0:
                death_saves = sheet.death_saves.model_dump()
                death_saves["successes"] = 0
                death_saves["failures"] = 0
                if isinstance(updated.get("defense"), dict):
                    updated["defense"]["death_saves"] = death_saves
                updated["death_saves"] = death_saves

            application = DamageApplication(
                damage_dealt=damage.amount,
                damage_type=damage.damage_type,
                hp_before=hp_before,
                hp_after=sheet.hp.current,
                is_unconscious=False,
                is_dead=False,
                is_healing=True,
                amount_applied=applied,
                chat_summary=(
                    f"Curación {applied} ({damage.damage_type}): "
                    f"PV {hp_before} → {sheet.hp.current}"
                ),
            )
            return updated, application

        result = apply_damage_pipeline(
            defender_sheet,
            amount=damage.amount,
            damage_type=damage.damage_type,
            is_critical=damage.is_critical,
        )
        updated = result["updated_sheet"]

        application = DamageApplication(
            damage_dealt=result["raw_amount"],
            damage_type=damage.damage_type,
            hp_before=result["hp_before"],
            hp_after=result["hp_after"],
            is_unconscious=result["hp_after"] == 0 and not result["is_dead"],
            is_dead=result["is_dead"],
            is_healing=False,
            amount_applied=result["amount_applied"],
            raw_amount=result["raw_amount"],
            modified_amount=result["modified_amount"],
            damage_modifier=result["damage_modifier"],
            is_critical=result["is_critical"],
            is_instant_death=result["is_instant_death"],
            death_save_failures_added=result["death_save_failures_added"],
            chat_summary=result["chat_summary"],
        )
        return updated, application
