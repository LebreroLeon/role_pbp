import pytest

from app.rules.dnd5e.mechanics import apply_death_save_roll, passive_perception, passive_perception_from_sheet
from app.rules.dnd5e.plugin import Dnd5ePlugin
from app.rules.base import RollContext


class TestPassivePerception:
    def test_base_without_proficiency(self):
        assert passive_perception(10, 2, perception_proficient=False) == 10

    def test_with_wis_mod_and_proficiency(self):
        # WIS 14 (+2) + prof (+2) + 10 = 14
        assert passive_perception(14, 2, perception_proficient=True) == 14

    def test_with_expertise(self):
        # WIS 14 (+2) + prof (+2) + expertise (+2) + 10 = 16
        assert passive_perception(14, 2, perception_proficient=True, perception_expertise=True) == 16

    def test_from_sheet_dict(self):
        sheet = {
            "abilities": {"wis": 12},
            "proficiency_bonus": 2,
            "skills": [{"name": "Perception", "proficient": True, "expertise": False}],
        }
        # WIS 12 (+1) + prof (+2) + 10 = 13
        assert passive_perception_from_sheet(sheet["abilities"], sheet["proficiency_bonus"], sheet["skills"]) == 13


class TestDeathSaveRoll:
    def test_success_on_ten_or_more(self):
        result = apply_death_save_roll(12, 0, 0, 0)
        assert result["successes"] == 1
        assert result["failures"] == 0
        assert result["is_success"] is True
        assert result["hp_current"] == 0

    def test_failure_below_ten(self):
        result = apply_death_save_roll(7, 0, 0, 0)
        assert result["successes"] == 0
        assert result["failures"] == 1
        assert result["is_success"] is False

    def test_natural_one_counts_two_failures(self):
        result = apply_death_save_roll(1, 0, 0, 0)
        assert result["failures"] == 2
        assert result["outcome"] == "critical_failure"

    def test_natural_twenty_restores_one_hp(self):
        result = apply_death_save_roll(20, 2, 1, 0)
        assert result["hp_current"] == 1
        assert result["successes"] == 0
        assert result["failures"] == 0
        assert result["outcome"] == "critical_success"

    def test_three_failures_marks_dead(self):
        result = apply_death_save_roll(5, 0, 2, 0)
        assert result["failures"] == 3
        assert result["dead"] is True

    def test_three_successes_stabilizes(self):
        result = apply_death_save_roll(15, 2, 0, 0)
        assert result["successes"] == 3
        assert result["stabilized"] is True


class TestDeathSavePluginRoll:
    def test_resolve_death_save_roll(self, monkeypatch):
        plugin = Dnd5ePlugin()
        sheet = plugin.default_pc_sheet()
        sheet["hp"]["current"] = 0
        sheet["death_saves"] = {"successes": 0, "failures": 0}
        monkeypatch.setattr("random.randint", lambda _a, b: 12 if b == 20 else 1)

        result = plugin.resolve_roll("death_save", sheet, RollContext())
        assert result.roll_type == "death_save"
        assert result.total == 12
        assert result.details["death_save_successes"] == 1
        assert result.details["death_save_failures"] == 0
        assert result.details["hp_current"] == 0
        assert "Salvación contra la muerte" in result.chat_summary

    def test_resolve_death_save_nat_20(self, monkeypatch):
        plugin = Dnd5ePlugin()
        sheet = plugin.default_pc_sheet()
        sheet["hp"]["current"] = 0
        sheet["death_saves"] = {"successes": 1, "failures": 2}
        monkeypatch.setattr("random.randint", lambda _a, b: 20 if b == 20 else 1)

        result = plugin.resolve_roll("death_save", sheet, RollContext())
        assert result.details["hp_current"] == 1
        assert result.details["death_save_successes"] == 0
        assert result.details["death_save_failures"] == 0
