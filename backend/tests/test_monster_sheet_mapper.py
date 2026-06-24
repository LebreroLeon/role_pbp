import json
from pathlib import Path

import pytest

from app.rules.dnd5e.monster_sheet_mapper import (
    MonsterSheetMapper,
    format_challenge_rating_display,
    open5e_key_to_slug,
)
from app.rules.dnd5e.schema import Dnd5eSheet

SNAPSHOT_PATH = Path(__file__).resolve().parents[1] / "data" / "dnd5e" / "srd-monsters.json"


@pytest.fixture
def goblin_creature() -> dict:
    monsters = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    for creature in monsters:
        if creature.get("key") == "srd_goblin":
            return creature
    pytest.skip("Goblin not found in SRD snapshot")


class TestMonsterSheetMapper:
    def test_goblin_stats_mapped_correctly(self, goblin_creature: dict):
        sheet = MonsterSheetMapper.map_creature(goblin_creature)
        validated = Dnd5eSheet.model_validate(sheet)

        assert validated.abilities.str == 8
        assert validated.abilities.dex == 14
        assert validated.abilities.con == 10
        assert validated.ac == 15
        assert validated.hp.max == 7
        assert validated.hp.current == 7
        assert validated.speed == "9 m (30 pies)"
        assert validated.initiative_modifier == 2
        assert validated.proficiency_bonus == 2
        assert len(validated.attacks) == 2
        assert validated.attacks[0].name == "Scimitar"
        assert validated.attacks[0].to_hit_bonus == 4
        assert validated.attacks[0].damage_dice == "1d6+2"
        assert validated.attacks[0].damage_type == "cortante"
        assert validated.attacks[1].name == "Shortbow"
        assert validated.attacks[1].damage_type == "perforante"

        stealth = next((skill for skill in validated.skills if skill.name == "Sigilo"), None)
        assert stealth is not None
        assert stealth.proficient is True
        assert stealth.expertise is True

    def test_open5e_key_to_slug(self):
        assert open5e_key_to_slug("srd_goblin") == "goblin"
        assert open5e_key_to_slug("custom-boss") == "custom-boss"

    def test_format_challenge_rating_display(self):
        assert format_challenge_rating_display(0.25) == "1/4"
        assert format_challenge_rating_display(0.25, raw="1/4 (50 PX)") == "1/4"
        assert format_challenge_rating_display(2) == "2"

    def test_maps_damage_resistances_from_srd(self):
        monsters = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
        fire_elemental = next(
            (creature for creature in monsters if "fire" in str(creature.get("key", "")).lower()),
            None,
        )
        if fire_elemental is None:
            fire_elemental = next(
                (
                    creature
                    for creature in monsters
                    if isinstance(creature.get("resistances_and_immunities"), dict)
                    and "fire" in (creature["resistances_and_immunities"].get("damage_immunities") or [])
                ),
                None,
            )
        assert fire_elemental is not None, "Need a fire-immune SRD creature for this test"

        sheet = MonsterSheetMapper.map_creature(fire_elemental)
        validated = Dnd5eSheet.model_validate(sheet)
        assert "fuego" in validated.damage_modifiers.immunities
