from app.services.dice import build_generic_roll_details, format_raw_roll_summary


class TestGenericDiceFormat:
    def test_format_raw_roll_summary_multi_dice(self):
        result = {"rolls": [12, 8, 14], "raw_result": 34, "final_result": 39}
        summary = format_raw_roll_summary("3d20+5", result)
        assert summary == "12 + 8 + 14 +5 = 39"

    def test_format_raw_roll_summary_single_die_with_modifier(self):
        result = {"rolls": [6], "raw_result": 6, "final_result": 9}
        summary = format_raw_roll_summary("1d8+3", result)
        assert summary == "1d8=6 +3 = 9"

    def test_build_generic_roll_details_multi_dice(self):
        result = {
            "rolls": [12, 8, 14],
            "raw_result": 34,
            "final_result": 39,
            "dice_sides": 20,
            "dice_count": 3,
        }
        details = build_generic_roll_details("3d20+5", result)
        assert details["rolls"] == [12, 8, 14]
        assert details["modifier"] == 5
        assert len(details["modifier_breakdown"]) == 2
        assert details["modifier_breakdown"][0]["rolls"] == [12, 8, 14]
        assert details["modifier_breakdown"][1]["label"] == "Modificador"
        assert details["modifier_breakdown"][1]["value"] == 5
