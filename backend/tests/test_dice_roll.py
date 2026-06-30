import pytest

from app.services import dice as dice_service


class TestParseDiceExpression:
    def test_single_die_with_modifier(self):
        groups, mod = dice_service._parse_dice_expression("1d8+3")
        assert groups == [(1, 8)]
        assert mod == 3

    def test_compound_dice_terms(self):
        groups, mod = dice_service._parse_dice_expression("1d20+3+2d6")
        assert groups == [(1, 20), (2, 6)]
        assert mod == 3

    def test_multiple_dice_and_trailing_modifier(self):
        groups, mod = dice_service._parse_dice_expression("2d6+1d4+2")
        assert groups == [(2, 6), (1, 4)]
        assert mod == 2

    def test_legacy_sides_shorthand(self):
        groups, mod = dice_service._parse_dice_expression("10+3")
        assert groups == [(1, 10)]
        assert mod == 3

    def test_rejects_empty(self):
        with pytest.raises(ValueError, match="empty"):
            dice_service._parse_dice_expression("")

    def test_rejects_garbage(self):
        with pytest.raises(ValueError, match="Invalid dice expression"):
            dice_service._parse_dice_expression("1d20++2d6")


class TestRollDiceCompound:
    def test_compound_expression_rolls_all_dice(self, monkeypatch):
        seq = iter([15, 4, 6])

        def fake_randint(_a: int, _b: int) -> int:
            return next(seq)

        monkeypatch.setattr("app.services.dice.random.randint", fake_randint)
        result = dice_service.roll_dice("1d20+3+2d6")
        assert result["rolls"] == [15, 4, 6]
        assert result["raw_result"] == 25
        assert result["final_result"] == 28
        assert result["inline_modifier"] == 3

    def test_multiple_dice_groups_no_flat_modifier(self, monkeypatch):
        seq = iter([3, 5, 2])

        def fake_randint(_a: int, _b: int) -> int:
            return next(seq)

        monkeypatch.setattr("app.services.dice.random.randint", fake_randint)
        result = dice_service.roll_dice("2d6+1d4+2")
        assert result["rolls"] == [3, 5, 2]
        assert result["raw_result"] == 10
        assert result["final_result"] == 12

    def test_single_term_still_works(self, monkeypatch):
        monkeypatch.setattr("app.services.dice.random.randint", lambda _a, _b: 6)
        result = dice_service.roll_dice("1d8+3")
        assert result["rolls"] == [6]
        assert result["final_result"] == 9

    def test_compound_not_single_d20(self):
        assert dice_service.is_single_d20_expression("1d20+3+2d6") is False

    def test_compound_d20_advantage_not_applied(self, monkeypatch):
        """Advantage only applies to a lone 1d20, not compound expressions."""
        seq = iter([10, 3, 4])

        def fake_randint(_a: int, _b: int) -> int:
            return next(seq)

        monkeypatch.setattr("app.services.dice.random.randint", fake_randint)
        result = dice_service.roll_dice(
            "1d20+3+2d6",
            game_system="dnd5e",
            advantage=True,
        )
        assert result["rolls"] == [10, 3, 4]
        assert "advantage" not in (result.get("roll_details") or {})
