import pytest

from app.rules.base import RollContext
from app.rules.dnd5e.plugin import Dnd5ePlugin
from app.rules.dnd5e.rolls import roll_d20
from app.services import dice as dice_service


class TestDnd5eAdvantage:
    def test_roll_d20_advantage_keeps_higher(self, monkeypatch):
        calls: list[int] = []

        def fake_randint(_a: int, _b: int) -> int:
            calls.append(len(calls))
            return [7, 18][len(calls) - 1]

        monkeypatch.setattr("app.rules.dnd5e.rolls.random.randint", fake_randint)
        rolls, chosen = roll_d20(advantage=True)
        assert rolls == [7, 18]
        assert chosen == 18

    def test_roll_d20_disadvantage_keeps_lower(self, monkeypatch):
        seq = iter([7, 18])

        def fake_randint(_a: int, _b: int) -> int:
            return next(seq)

        monkeypatch.setattr("app.rules.dnd5e.rolls.random.randint", fake_randint)
        rolls, chosen = roll_d20(disadvantage=True)
        assert rolls == [7, 18]
        assert chosen == 7

    def test_advantage_cancels_disadvantage(self, monkeypatch):
        monkeypatch.setattr("app.rules.dnd5e.rolls.random.randint", lambda _a, _b: 12)
        rolls, chosen = roll_d20(advantage=True, disadvantage=True)
        assert rolls == [12]
        assert chosen == 12

    def test_skill_check_with_advantage(self, monkeypatch):
        plugin = Dnd5ePlugin()
        sheet = plugin.default_pc_sheet()
        seq = iter([4, 17])

        def fake_randint(_a: int, _b: int) -> int:
            return next(seq)

        monkeypatch.setattr("random.randint", fake_randint)
        result = plugin.resolve_roll(
            "skill_check",
            sheet,
            RollContext(skill="perception", advantage=True),
        )
        assert result.rolls == [4, 17]
        assert result.details["natural_roll"] == 17
        assert result.details["advantage"] is True
        assert "2d20 (ventaja)" in result.chat_summary

    def test_generic_d20_advantage_via_dice_service(self, monkeypatch):
        seq = iter([6, 19])

        def fake_randint(_a: int, _b: int) -> int:
            return next(seq)

        monkeypatch.setattr("app.rules.dnd5e.rolls.random.randint", fake_randint)
        payload = dice_service.roll_dice(
            "1d20+2",
            game_system="dnd5e",
            advantage=True,
        )
        assert payload["rolls"] == [6, 19]
        assert payload["final_result"] == 21
        assert payload["roll_details"]["advantage"] is True
        assert payload["roll_details"]["natural_roll"] == 19

    def test_is_single_d20_expression(self):
        assert dice_service.is_single_d20_expression("1d20") is True
        assert dice_service.is_single_d20_expression("1d20+3") is True
        assert dice_service.is_single_d20_expression("2d20") is False
        assert dice_service.is_single_d20_expression("1d8") is False
