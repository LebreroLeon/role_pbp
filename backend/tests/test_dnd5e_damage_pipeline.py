import pytest

from app.rules.base import AttackContext, DamageResult
from app.rules.dnd5e.mechanics import (
    apply_damage_modifiers,
    apply_damage_pipeline,
    double_damage_dice,
)
from app.rules.dnd5e.plugin import Dnd5ePlugin


@pytest.fixture
def plugin() -> Dnd5ePlugin:
    return Dnd5ePlugin()


class TestDoubleDamageDice:
    def test_doubles_single_die_with_modifier(self):
        assert double_damage_dice("1d8+3") == "2d8+3"

    def test_doubles_multiple_dice(self):
        assert double_damage_dice("2d6") == "4d6"


class TestDamageModifiers:
    def test_resistance_halves_floor(self):
        sheet = {"damage_modifiers": {"resistances": ["fuego"], "vulnerabilities": [], "immunities": []}}
        amount, label = apply_damage_modifiers(14, "fuego", sheet)
        assert amount == 7
        assert label == "resistencia"

    def test_vulnerability_doubles(self):
        sheet = {"damage_modifiers": {"resistances": [], "vulnerabilities": ["fuego"], "immunities": []}}
        amount, label = apply_damage_modifiers(14, "fuego", sheet)
        assert amount == 28
        assert label == "vulnerabilidad"

    def test_immunity_zeros(self):
        sheet = {"damage_modifiers": {"resistances": [], "vulnerabilities": [], "immunities": ["fuego"]}}
        amount, label = apply_damage_modifiers(14, "fuego", sheet)
        assert amount == 0
        assert label == "inmunidad"


class TestApplyDamagePipeline:
    def test_instant_death_overflow(self):
        sheet = {"hp": {"max": 24, "current": 10, "temp": 0}, "death_saves": {"successes": 0, "failures": 0}}
        result = apply_damage_pipeline(sheet, amount=34, damage_type="contundente")
        assert result["is_instant_death"] is True
        assert result["is_dead"] is True
        assert result["hp_after"] == 0

    def test_damage_at_zero_hp_adds_failure(self):
        sheet = {"hp": {"max": 24, "current": 0, "temp": 0}, "death_saves": {"successes": 0, "failures": 0}}
        result = apply_damage_pipeline(sheet, amount=5, damage_type="contundente")
        assert result["death_save_failures_added"] == 1
        assert result["updated_sheet"]["death_saves"]["failures"] == 1

    def test_damage_at_zero_hp_critical_adds_two_failures(self):
        sheet = {"hp": {"max": 24, "current": 0, "temp": 0}, "death_saves": {"successes": 0, "failures": 0}}
        result = apply_damage_pipeline(sheet, amount=5, damage_type="contundente", is_critical=True)
        assert result["death_save_failures_added"] == 2
        assert result["updated_sheet"]["death_saves"]["failures"] == 2

    def test_resistance_in_pipeline(self):
        sheet = {
            "hp": {"max": 20, "current": 20, "temp": 0},
            "death_saves": {"successes": 0, "failures": 0},
            "damage_modifiers": {"resistances": ["fuego"], "vulnerabilities": [], "immunities": []},
        }
        result = apply_damage_pipeline(sheet, amount=14, damage_type="fuego")
        assert result["raw_amount"] == 14
        assert result["modified_amount"] == 7
        assert result["hp_after"] == 13


class TestCriticalAttack:
    def test_nat_20_doubles_damage_dice(self, plugin: Dnd5ePlugin, monkeypatch):
        rolls = iter([20, 5, 5])

        def fake_randint(a: int, b: int) -> int:
            return next(rolls)

        monkeypatch.setattr("random.randint", fake_randint)

        attacker = plugin.default_pc_sheet()
        defender = plugin.default_npc_sheet("medium")
        attack = plugin.resolve_attack(
            attacker,
            defender,
            "Longsword",
            AttackContext(target_ac=10),
        )
        assert attack.hit is True
        assert attack.attack_roll.details.get("is_critical") is True
        assert attack.damage is not None
        assert attack.damage.is_critical is True
        assert attack.damage.expression == "2d8+3"
        assert attack.damage.amount == 13  # 5 + 5 + 3

    def test_apply_critical_damage_via_plugin(self, plugin: Dnd5ePlugin):
        defender = {"hp": {"max": 24, "current": 24, "temp": 0}}
        updated, application = plugin.apply_damage(
            defender,
            DamageResult(
                amount=13,
                expression="2d8+3",
                rolls=[5, 5],
                damage_type="cortante",
                modifier=3,
                is_critical=True,
            ),
        )
        assert application.hp_after == 11
        assert updated["hp"]["current"] == 11
