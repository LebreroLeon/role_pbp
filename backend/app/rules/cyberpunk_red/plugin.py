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
from app.rules.cyberpunk_red.schema import (
    CYBERPUNK_STATS,
    CyberpunkRedSheet,
    SUPPORTED_ROLL_TYPES,
    WeaponEntry,
)
from app.services import dice as dice_service


def _normalize_key(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


def _parse_sheet(actor_sheet: dict) -> CyberpunkRedSheet:
    return CyberpunkRedSheet.model_validate(actor_sheet)


def _skill_entry(sheet: CyberpunkRedSheet, skill_name: str) -> tuple[str, int]:
    key = _normalize_key(skill_name)
    for entry in sheet.skills:
        if _normalize_key(entry.name) == key:
            stat = _normalize_key(entry.stat)
            if stat not in CYBERPUNK_STATS:
                stat = "ref"
            return stat, entry.rank
    raise ValueError(f"Unknown skill: {skill_name}")


def _roll_d10_pool(pool_size: int) -> tuple[list[int], int]:
    size = max(0, pool_size)
    rolls = [random.randint(1, 10) for _ in range(size)]
    successes = sum(1 for roll in rolls if roll >= 6)
    return rolls, successes


def _pool_expression(pool_size: int) -> str:
    return f"{pool_size}d10" if pool_size else "0d10"


def _find_weapon(sheet: CyberpunkRedSheet, context: RollContext | AttackContext) -> tuple[int, WeaponEntry]:
    if isinstance(context, RollContext) and context.attack_index is not None:
        idx = context.attack_index
        if idx < 0 or idx >= len(sheet.weapons):
            raise ValueError(f"Weapon index out of range: {idx}")
        return idx, sheet.weapons[idx]

    attack_name = context.attack_name if isinstance(context, AttackContext) else context.attack_name
    if attack_name:
        key = _normalize_key(attack_name)
        for idx, weapon in enumerate(sheet.weapons):
            if _normalize_key(weapon.name) == key:
                return idx, weapon
        raise ValueError(f"Weapon not found: {attack_name}")

    if sheet.weapons:
        return 0, sheet.weapons[0]

    raise ValueError("No weapons defined on sheet")


class CyberpunkRedPlugin(GameSystemPlugin):
    system_id = "cyberpunk_red"
    dice_mode = "dice_pool"
    sheet_schema_version = "1.0.0"

    def validate_pc_sheet(self, sheet: dict) -> BaseModel:
        return CyberpunkRedSheet.model_validate(sheet)

    def validate_npc_sheet(self, sheet: dict) -> BaseModel:
        return CyberpunkRedSheet.model_validate(sheet)

    def default_pc_sheet(self) -> dict:
        return CyberpunkRedSheet(
            stats={
                "int": 4,
                "ref": 6,
                "tech": 4,
                "cool": 5,
                "attr": 4,
                "luck": 4,
                "move": 4,
                "body": 5,
                "emp": 4,
            },
            skills=[
                {"name": "handgun", "stat": "ref", "rank": 4},
                {"name": "evasion", "stat": "ref", "rank": 2},
                {"name": "athletics", "stat": "body", "rank": 2},
            ],
            hp={"max": 40, "current": 40},
            armor={"head": 0, "body": 11},
            weapons=[
                {
                    "name": "Heavy Pistol",
                    "stat": "ref",
                    "skill": "handgun",
                    "damage_dice": "2d6",
                    "damage_type": "ballistic",
                }
            ],
        ).model_dump()

    def default_npc_sheet(self, power_scale: str = "medium") -> dict:
        hp_by_scale = {"weak": 20, "medium": 40, "strong": 60, "boss": 80}
        max_hp = hp_by_scale.get(power_scale, 40)
        return CyberpunkRedSheet(
            stats={"ref": 5, "body": 4, "cool": 3},
            skills=[
                {"name": "handgun", "stat": "ref", "rank": 2},
                {"name": "evasion", "stat": "ref", "rank": 1},
            ],
            hp={"max": max_hp, "current": max_hp},
            armor={"head": 0, "body": 7},
            weapons=[
                {
                    "name": "Knife",
                    "stat": "ref",
                    "skill": "melee",
                    "damage_dice": "1d6",
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

        if normalized == "skill_check":
            return self._resolve_skill_check(sheet, context)
        if normalized == "stat_check":
            return self._resolve_stat_check(sheet, context)
        if normalized in {"attack_roll", "attack"}:
            return self._resolve_attack_roll(sheet, context)
        if normalized == "damage":
            return self._resolve_damage(sheet, context)
        if normalized == "initiative":
            return self._resolve_initiative(sheet, context)

        raise ValueError(
            f"Unsupported roll_type '{roll_type}' for cyberpunk_red. "
            f"Supported: {', '.join(SUPPORTED_ROLL_TYPES)}"
        )

    def _resolve_skill_check(self, sheet: CyberpunkRedSheet, context: RollContext) -> RollResult:
        if not context.skill:
            raise ValueError("skill_check requires context.skill")
        stat, rank = _skill_entry(sheet, context.skill)
        pool = sheet.stats.score(stat) + rank
        if context.modifier_override is not None:
            pool = max(0, pool + context.modifier_override)
        return self._pool_roll(
            "skill_check",
            pool,
            context,
            stat=stat,
            skill=context.skill,
            skill_rank=rank,
        )

    def _resolve_stat_check(self, sheet: CyberpunkRedSheet, context: RollContext) -> RollResult:
        if not context.ability:
            raise ValueError("stat_check requires context.ability")
        stat = _normalize_key(context.ability)
        pool = sheet.stats.score(stat)
        if context.modifier_override is not None:
            pool = max(0, pool + context.modifier_override)
        return self._pool_roll("stat_check", pool, context, stat=stat)

    def _resolve_attack_roll(self, sheet: CyberpunkRedSheet, context: RollContext) -> RollResult:
        if context.skill:
            stat, rank = _skill_entry(sheet, context.skill)
        elif context.attack_name or context.attack_index is not None:
            _, weapon = _find_weapon(sheet, context)
            stat = _normalize_key(weapon.stat)
            try:
                _, rank = _skill_entry(sheet, weapon.skill)
            except ValueError:
                rank = 0
        else:
            stat, rank = "ref", 0

        pool = sheet.stats.score(stat) + rank
        rolls, successes = _roll_d10_pool(pool)
        hit = None
        target_evasion = context.target_ac

        if target_evasion is not None:
            hit = successes >= target_evasion
            success = hit
        else:
            success = successes >= (context.dc or 1)

        details: dict = {
            "stat": stat,
            "skill": context.skill,
            "pool_size": pool,
            "successes": successes,
            "target_evasion": target_evasion,
            "dc": context.dc,
        }

        summary = f"Ataque ({stat}+{rank}): {_pool_expression(pool)} → {successes} éxitos"
        if target_evasion is not None:
            summary += f" vs evasión {target_evasion} — {'impacto' if hit else 'fallo'}"
        elif context.dc is not None:
            summary += f" vs CD {context.dc} — {'éxito' if success else 'fallo'}"

        return RollResult(
            roll_type="attack_roll",
            expression=_pool_expression(pool),
            rolls=rolls,
            total=successes,
            success=success,
            details=details,
            chat_summary=summary,
        )

    def _resolve_damage(self, sheet: CyberpunkRedSheet, context: RollContext) -> RollResult:
        if context.expression:
            expression = context.expression
            damage_type = "untyped"
        else:
            _, weapon = _find_weapon(sheet, context)
            expression = weapon.damage_dice
            damage_type = weapon.damage_type

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
            },
            chat_summary=f"Daño ({damage_type}): {expression} = {total}",
        )

    def _resolve_initiative(self, sheet: CyberpunkRedSheet, context: RollContext) -> RollResult:
        ref = sheet.stats.score("ref")
        roll = random.randint(1, 10)
        modifier = context.modifier_override or 0
        total = ref + roll + modifier
        return RollResult(
            roll_type="initiative",
            expression=f"1d10+{ref}",
            rolls=[roll],
            total=total,
            success=None,
            details={"ref": ref, "d10": roll, "modifier": modifier},
            chat_summary=f"Iniciativa: REF {ref} + d10({roll}) = {total}",
        )

    def _pool_roll(
        self,
        roll_type: str,
        pool_size: int,
        context: RollContext,
        **extra_details: object,
    ) -> RollResult:
        rolls, successes = _roll_d10_pool(pool_size)
        threshold = context.dc if context.dc is not None else 1
        success = successes >= threshold

        details: dict = {
            "pool_size": pool_size,
            "successes": successes,
            "threshold": threshold,
        }
        details.update(extra_details)
        if context.dc is not None:
            details["dc"] = context.dc

        label = roll_type.replace("_", " ")
        summary = f"{label}: {_pool_expression(pool_size)} → {successes} éxitos"
        if context.dc is not None:
            summary += f" vs CD {context.dc} — {'éxito' if success else 'fallo'}"

        return RollResult(
            roll_type=roll_type,
            expression=_pool_expression(pool_size),
            rolls=rolls,
            total=successes,
            success=success,
            details=details,
            chat_summary=summary,
        )

    def _evasion_threshold(self, sheet: CyberpunkRedSheet) -> int:
        try:
            _, rank = _skill_entry(sheet, "evasion")
        except ValueError:
            rank = 0
        return max(1, sheet.stats.score("ref") + rank)

    def resolve_attack(
        self,
        attacker_sheet: dict,
        defender_sheet: dict,
        weapon_or_attack_id: str | None,
        context: AttackContext,
    ) -> AttackResult:
        attacker = _parse_sheet(attacker_sheet)
        defender = _parse_sheet(defender_sheet)

        if weapon_or_attack_id or context.attack_name or context.attack_index is not None:
            _, weapon = _find_weapon(
                attacker,
                AttackContext(
                    attack_name=weapon_or_attack_id or context.attack_name,
                    attack_index=context.attack_index,
                ),
            )
            skill_name = weapon.skill
            weapon_name = weapon.name
        else:
            skill_name = "handgun"
            weapon_name = "ataque"

        attacker_pool = 0
        try:
            stat, rank = _skill_entry(attacker, skill_name)
            attacker_pool = attacker.stats.score(stat) + rank
        except ValueError:
            attacker_pool = attacker.stats.score("ref")

        defender_pool = self._evasion_threshold(defender)
        attacker_rolls, attacker_successes = _roll_d10_pool(attacker_pool)
        defender_rolls, defender_successes = _roll_d10_pool(defender_pool)
        hit = attacker_successes > defender_successes

        attack_roll = RollResult(
            roll_type="attack_roll",
            expression=_pool_expression(attacker_pool),
            rolls=attacker_rolls,
            total=attacker_successes,
            success=hit,
            details={
                "skill": skill_name,
                "weapon": weapon_name,
                "attacker_successes": attacker_successes,
                "defender_successes": defender_successes,
                "defender_pool": defender_pool,
                "defender_rolls": defender_rolls,
                "hit": hit,
            },
            chat_summary=(
                f"Ataque ({weapon_name}): {attacker_successes} vs evasión {defender_successes} — "
                f"{'impacto' if hit else 'fallo'}"
            ),
        )

        damage_result = None
        if hit:
            damage_roll = self.resolve_roll(
                "damage",
                attacker_sheet,
                RollContext(
                    attack_name=weapon_or_attack_id or context.attack_name or weapon_name,
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

        if hit and damage_result:
            summary = (
                f"{weapon_name}: {attacker_successes} vs {defender_successes} — impacto. "
                f"{damage_result.amount} {damage_result.damage_type}."
            )
        else:
            summary = f"{weapon_name}: {attacker_successes} vs {defender_successes} — fallo."

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
                f"HP {hp_before} → {sheet.hp.current}"
            ),
        )
        return updated, application
