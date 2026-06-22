import json
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.monster_catalog import SystemMonsterCatalog
from app.schemas.entities import EntityType
from app.services.monster_spawn import (
    _next_monster_names,
    apply_rolled_hit_points,
    build_npc_document_from_catalog,
    roll_monster_hit_points,
    spawn_monsters,
)
from app.services.entities import validate_entity_document

SNAPSHOT_PATH = __import__("pathlib").Path(__file__).resolve().parents[1] / "data" / "dnd5e" / "srd-monsters.json"


@pytest.fixture
def goblin_catalog_entry() -> SystemMonsterCatalog:
    monsters = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    goblin = next(creature for creature in monsters if creature.get("key") == "srd_goblin")
    from app.core.seed_monsters import build_catalog_row

    row = build_catalog_row(goblin)
    entry = SystemMonsterCatalog(**row)
    return entry


class TestMonsterNaming:
    def test_next_monster_names_skips_existing_numbers(self):
        names = _next_monster_names("Goblin", ["Goblin 1", "Goblin 2", "Orc 1"], 3)
        assert names == ["Goblin 3", "Goblin 4", "Goblin 5"]


class TestBuildNpcDocument:
    def test_builds_hidden_hostile_npc_with_valid_sheet(self, goblin_catalog_entry: SystemMonsterCatalog):
        document = build_npc_document_from_catalog(
            goblin_catalog_entry,
            name="Goblin 1",
            player_visibility="hidden",
            attitude="hostile",
        )
        validated = validate_entity_document(EntityType.NPC, document)

        assert validated.identity.name == "Goblin 1"
        assert validated.state_flags.player_visibility == "hidden"
        assert validated.state_flags.hidden_from_players is True
        assert validated.state_flags.attitude_towards_party == "hostile"
        assert validated.state_flags.compendium_tier == "combat"
        assert validated.system_mechanics.system_id == "dnd5e"
        assert validated.system_mechanics.sheet["ac"] == 15

    def test_spawn_rolls_hit_dice_for_hp(self, goblin_catalog_entry: SystemMonsterCatalog):
        goblin_catalog_entry.sheet_template["hit_dice"] = "2d6"
        goblin_catalog_entry.sheet_template["hp"] = {"max": 7, "current": 7, "temp": 0}

        rolled_values: set[int] = set()
        for _ in range(30):
            document = build_npc_document_from_catalog(
                goblin_catalog_entry,
                name="Goblin 1",
            )
            hp = document["system_mechanics"]["sheet"]["hp"]
            assert 2 <= hp["current"] <= 12
            assert hp["current"] == hp["max"]
            rolled_values.add(hp["current"])

        assert len(rolled_values) > 1


class TestRollMonsterHitPoints:
    def test_roll_monster_hit_points_uses_hit_dice(self):
        current, maximum = roll_monster_hit_points({"hit_dice": "2d6", "hp": {"max": 7, "current": 7}})
        assert 2 <= current <= 12
        assert current == maximum

    def test_apply_rolled_hit_points_updates_sheet(self):
        sheet = apply_rolled_hit_points({"hit_dice": "2d6", "hp": {"max": 7, "current": 7, "temp": 0}})
        assert sheet["hp"]["current"] == sheet["hp"]["max"]
        assert 2 <= sheet["hp"]["current"] <= 12


@pytest.mark.asyncio
async def test_spawn_monsters_creates_numbered_goblins(goblin_catalog_entry: SystemMonsterCatalog):
    campaign_id = uuid.uuid4()
    campaign = MagicMock()
    campaign.game_system = "dnd5e"

    db = AsyncMock()

    async def scalar_side_effect(stmt):
        # First call: get campaign; second: get catalog entry
        if not hasattr(scalar_side_effect, "calls"):
            scalar_side_effect.calls = 0
        scalar_side_effect.calls += 1
        if scalar_side_effect.calls == 1:
            return campaign
        if scalar_side_effect.calls == 2:
            return goblin_catalog_entry
        return None

    db.scalar = AsyncMock(side_effect=scalar_side_effect)

    scalars_result = MagicMock()
    scalars_result.all.return_value = []
    db.scalars = AsyncMock(return_value=scalars_result)

    created = await spawn_monsters(
        db,
        campaign_id=campaign_id,
        slug="goblin",
        count=5,
        player_visibility="hidden",
        attitude="hostile",
    )

    assert len(created) == 5
    assert db.add.call_count == 5
    db.commit.assert_awaited_once()

    added_entities = [call.args[0] for call in db.add.call_args_list]
    names = [entity.document["identity"]["name"] for entity in added_entities]
    assert names == ["Goblin 1", "Goblin 2", "Goblin 3", "Goblin 4", "Goblin 5"]
    for entity in added_entities:
        assert entity.document["state_flags"]["player_visibility"] == "hidden"
        assert entity.document["state_flags"]["hidden_from_players"] is True
        hp = entity.document["system_mechanics"]["sheet"]["hp"]
        assert 2 <= hp["max"] <= 12
        assert hp["current"] == hp["max"]
