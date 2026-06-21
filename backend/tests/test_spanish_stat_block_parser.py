import json
from pathlib import Path

import pytest

from app.rules.dnd5e.schema import Dnd5eSheet
from app.rules.dnd5e.spanish_stat_block_parser import (
    build_catalog_row_from_parsed,
    extract_monster_block_from_page,
    extract_monster_lore_from_pages,
    parse_spanish_stat_block,
    validate_parsed_sheet,
)

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "goblin_mm_edge_page178.txt"
LORE_FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "goblin_mm_edge_page177.txt"
SOURCE_LABEL = "Manual de Monstruos (Edge)"


@pytest.fixture
def goblin_page_text() -> str:
    return FIXTURE_PATH.read_text(encoding="utf-8")


@pytest.fixture
def goblin_lore_page_text() -> str:
    return LORE_FIXTURE_PATH.read_text(encoding="utf-8")


@pytest.fixture
def goblin_pages(goblin_lore_page_text: str, goblin_page_text: str) -> dict[int, str]:
    svirfneblin_page = (
        "SVIRFNEBLIN\n"
        "Humanoide Pequeño (gnomo), neutral bueno\n"
        "Los gnomos de las profundidades habitan el Underdark.\n"
    )
    return {176: svirfneblin_page, 177: goblin_lore_page_text, 178: goblin_page_text}


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
        assert parsed_goblin.challenge_rating_raw == "1/4"
        assert parsed_goblin.type_line == "Humanoide Pequeño (trasgo), neutral malvado"
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

    def test_catalog_row_has_provenance_fields(self, parsed_goblin, goblin_pages):
        lore = extract_monster_lore_from_pages(
            goblin_pages,
            stat_page=178,
            monster_name="Goblin",
        )
        row = build_catalog_row_from_parsed(
            parsed_goblin,
            slug="goblin-mm-edge",
            source_document="mm-edge-es",
            source_label=SOURCE_LABEL,
            lore_text=lore,
        )
        assert row["slug"] == "goblin-mm-edge"
        assert row["source_document"] == "mm-edge-es"
        assert row["source_label"] == SOURCE_LABEL
        assert row["narrative_template"]["concept"] == "Humanoide Pequeño (trasgo), neutral malvado"
        assert "CR 0.25" not in row["narrative_template"]["concept"]
        assert "mirada maliciosa" in row["narrative_template"]["public_description"]
        assert f"Fuente: {SOURCE_LABEL}" in row["sheet_template"]["features_traits"]
        assert row["sheet_template"]["hit_dice"] == "2d6"
        Dnd5eSheet.model_validate(row["sheet_template"])

    def test_extracts_goblin_lore_from_previous_page(self, goblin_pages):
        lore = extract_monster_lore_from_pages(
            goblin_pages,
            stat_page=178,
            monster_name="Goblin",
        )
        assert "trasgos" in lore.lower()
        assert "mirada maliciosa" in lore.lower()
        assert "GOBLIN" not in lore
        assert "Clase de Armadura" not in lore
        assert "svirfneblin" not in lore.lower()
        assert "underdark" not in lore.lower()


NEOTHELIDO_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "neothelido_volo_page177.txt"
OBLEX_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "oblex_anciano_multiverse_page213.txt"
VOLO_SOURCE = "Guía de Monstruos de Volo (Edge)"
MULTIVERSE_SOURCE = "Monstruos del Multiverso (Edge)"


class TestVoloNeothelidoParser:
    def test_parses_neothelido_core_stats(self):
        block = NEOTHELIDO_FIXTURE.read_text(encoding="utf-8")
        parsed = parse_spanish_stat_block(block)
        assert parsed.name == "Neothelido"
        assert parsed.armor_class == 16
        assert parsed.hit_points == 325
        assert parsed.hit_dice == "21d20 + 105"
        assert parsed.challenge_rating == 13
        assert parsed.type_line == "Aberración Gargantuesca, caótico malvado"
        assert parsed.ability_scores["strength"] == 27

    def test_parses_neothelido_tentacle_attack(self):
        parsed = parse_spanish_stat_block(NEOTHELIDO_FIXTURE.read_text(encoding="utf-8"))
        tentacles = next(action for action in parsed.actions if "Tentáculos" in action["name"])
        attack = tentacles["attacks"][0]
        assert attack["to_hit_mod"] == 13
        assert attack["damage_die_count"] == 3
        assert attack["damage_die_type"] == "D8"

    def test_neothelido_catalog_row(self):
        block = NEOTHELIDO_FIXTURE.read_text(encoding="utf-8")
        parsed = parse_spanish_stat_block(block)
        row = build_catalog_row_from_parsed(
            parsed,
            slug="neothelido-volo-edge",
            source_document="volo-edge-es",
            source_label=VOLO_SOURCE,
            lore_text="Un neothélido emerge de una colonia illithid colapsada.",
        )
        assert row["slug"] == "neothelido-volo-edge"
        assert row["narrative_template"]["concept"] == parsed.type_line
        assert row["sheet_template"]["hit_dice"] == "21d20 + 105"
        assert f"Fuente: {VOLO_SOURCE}" in row["sheet_template"]["features_traits"]
        Dnd5eSheet.model_validate(row["sheet_template"])


class TestMultiverseOblexParser:
    def test_parses_oblex_anciano_core_stats(self):
        block = OBLEX_FIXTURE.read_text(encoding="utf-8")
        parsed = parse_spanish_stat_block(block)
        assert parsed.name == "Oblex Anciano"
        assert parsed.armor_class == 16
        assert parsed.hit_points == 115
        assert parsed.hit_dice == "10d12 + 50"
        assert parsed.challenge_rating == 10
        assert parsed.creature_type == "Cieno"
        assert parsed.size == "Enorme"

    def test_parses_oblex_pseudopod_attack(self):
        parsed = parse_spanish_stat_block(OBLEX_FIXTURE.read_text(encoding="utf-8"))
        pseudopod = next(action for action in parsed.actions if "Pseud" in action["name"])
        attack = pseudopod["attacks"][0]
        assert attack["to_hit_mod"] == 7
        assert attack["damage_die_count"] == 4
        assert attack["damage_die_type"] == "D6"

    def test_oblex_catalog_row(self):
        block = OBLEX_FIXTURE.read_text(encoding="utf-8")
        parsed = parse_spanish_stat_block(block)
        row = build_catalog_row_from_parsed(
            parsed,
            slug="oblex-anciano-multiverse-edge",
            source_document="multiverse-edge-es",
            source_label=MULTIVERSE_SOURCE,
            lore_text="Los oblexes se alimentan de pensamientos y recuerdos.",
        )
        assert row["slug"] == "oblex-anciano-multiverse-edge"
        assert row["sheet_template"]["hit_dice"] == "10d12 + 50"
        assert len(row["sheet_template"]["attacks"]) >= 1
        assert f"Fuente: {MULTIVERSE_SOURCE}" in row["sheet_template"]["features_traits"]
        Dnd5eSheet.model_validate(row["sheet_template"])
