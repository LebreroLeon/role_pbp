import pytest

from app.rules.dnd5e.damage_types import normalize_damage_type
from app.rules.dnd5e.schema import Dnd5eSheet, normalize_sheet_identity, parse_class_level


class TestParseClassLevel:
    def test_parses_class_and_level(self):
        assert parse_class_level("Guerrero 3") == ("Guerrero", 3)
        assert parse_class_level("Fighter 5") == ("Fighter", 5)

    def test_class_only_defaults_level(self):
        assert parse_class_level("Monje") == ("Monje", 1)

    def test_empty_values(self):
        assert parse_class_level("") == ("", 1)


class TestNormalizeSheetIdentity:
    def test_migrates_class_level(self):
        identity = normalize_sheet_identity(
            {"class_level": "Guerrero 3", "background": "Soldado", "race": "Humano", "alignment": "LB"}
        )
        assert identity["class"] == "Guerrero"
        assert identity["level"] == 3

    def test_prefers_explicit_class_and_level(self):
        identity = normalize_sheet_identity(
            {"class": "Mago", "level": 7, "class_level": "Guerrero 3", "background": "", "race": "", "alignment": ""}
        )
        assert identity["class"] == "Mago"
        assert identity["level"] == 7


class TestNormalizeDamageType:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("slashing", "cortante"),
            ("contundente", "contundente"),
            ("Relámpago", "relampago"),
            ("", "contundente"),
        ],
    )
    def test_maps_aliases(self, raw: str, expected: str):
        assert normalize_damage_type(raw) == expected


class TestDnd5eSheetIdentityAndAttacks:
    def test_roleplay_inspiration_defaults_false(self):
        sheet = Dnd5eSheet.model_validate({})
        assert sheet.roleplay.inspiration is False

    def test_roleplay_inspiration_persists(self):
        sheet = Dnd5eSheet.model_validate({"roleplay": {"inspiration": True}})
        assert sheet.roleplay.inspiration is True

    def test_validate_legacy_class_level_and_english_damage(self):
        sheet = Dnd5eSheet.model_validate(
            {
                "identity": {"class_level": "Pícaro 4", "background": "", "race": "Elfo", "alignment": "CN"},
                "attacks": [
                    {
                        "name": "Daga",
                        "to_hit_bonus": 4,
                        "damage_dice": "1d4",
                        "damage_type": "piercing",
                    }
                ],
            }
        )
        assert sheet.identity.class_ == "Pícaro"
        assert sheet.identity.level == 4
        assert sheet.attacks[0].damage_type == "perforante"
        assert sheet.attacks[0].effect_type == "damage"

    def test_validate_healing_attack(self):
        sheet = Dnd5eSheet.model_validate(
            {
                "attacks": [
                    {
                        "name": "Curar heridas",
                        "damage_dice": "1d8+3",
                        "damage_type": "radiante",
                        "effect_type": "healing",
                    }
                ]
            }
        )
        assert sheet.attacks[0].effect_type == "healing"
