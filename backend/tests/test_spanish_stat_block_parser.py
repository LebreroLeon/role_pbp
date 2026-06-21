import json
from pathlib import Path

import pytest

from app.rules.dnd5e.schema import Dnd5eSheet
from app.rules.dnd5e.spanish_stat_block_parser import (
    build_catalog_row_from_parsed,
    extract_monster_block_from_page,
    parse_spanish_stat_block,
    validate_parsed_sheet,
)

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "goblin_mm_edge_page178.txt"
SOURCE_LABEL = "Manual de Monstruos (Edge)"


@pytest.fixture
def goblin_page_text() -> str:
    return FIXTURE_PATH.read_text(encoding="utf-8")


@pytest.fixture
def goblin_block(goblin_page_text: str) -> str:
    return extract_monster_block_from_page(goblin_page_text, "Goblin")


@pytest.fixture
def parsed_goblin(goblin_block: str):
    return parse_spanish_stat_block(goblin_block)


class TestSpanishStatBlockParser:
    def test_extracts_goblin_block_from_noisy_page(self, goblin_page_text: str):
        block = extract_monster_block_from_page(goblin_page_text, "Goblin")
        assert block.startswith("GOBLIN")
        assert "JEFE GOBLIN" not in block

    def test_parses_goblin_core_stats(self, parsed_goblin):
        assert parsed_goblin.name == "Goblin"
        assert parsed_goblin.armor_class == 15
        assert parsed_goblin.hit_points == 7
        assert parsed_goblin.hit_dice == "2d6"
        assert parsed_goblin.challenge_rating == 0.25
        assert parsed_goblin.ability_scores["dexterity"] == 14
        assert parsed_goblin.skill_bonuses["stealth"] == 6

    def test_parses_goblin_scimitar_attack(self, parsed_goblin):
        scimitar = next(action for action in parsed_goblin.actions if "Cimitarra" in action["name"])
        attack = scimitar["attacks"][0]
        assert attack["to_hit_mod"] == 4
        assert attack["damage_die_count"] == 1
        assert attack["damage_bonus"] == 2

    def test_maps_to_valid_sheet_with_provenance(self, parsed_goblin):
        sheet = validate_parsed_sheet(parsed_goblin, source_label=SOURCE_LABEL)
        assert sheet.ac == 15
        assert sheet.hp.max == 7
        assert len(sheet.attacks) >= 1
        scimitar = next(attack for attack in sheet.attacks if "Cimitarra" in attack.name)
        assert scimitar.to_hit_bonus == 4
        assert scimitar.damage_dice == "1d6+2"
        assert scimitar.damage_type == "cortante"
        assert f"Fuente: {SOURCE_LABEL}" in sheet.features_traits

    def test_catalog_row_has_provenance_fields(self, parsed_goblin):
        row = build_catalog_row_from_parsed(
            parsed_goblin,
            slug="goblin-mm-edge",
            source_document="mm-edge-es",
            source_label=SOURCE_LABEL,
        )
        assert row["slug"] == "goblin-mm-edge"
        assert row["source_document"] == "mm-edge-es"
        assert row["source_label"] == SOURCE_LABEL
        assert f"Fuente: {SOURCE_LABEL}" in row["sheet_template"]["features_traits"]
        Dnd5eSheet.model_validate(row["sheet_template"])
