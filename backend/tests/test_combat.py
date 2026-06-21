import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.campaign import Campaign, CampaignEntity
from app.rules.dnd5e.plugin import Dnd5ePlugin
from app.schemas.scene import SceneContext, SceneMetadata, SceneState, StateFlags
from app.services.combat_resolver import (
    CombatResolverError,
    assert_attacker_permission,
    entity_display_name,
    execute_attack,
    fetch_scene_combat_entities,
    get_combat_plugin,
    resolve_entity_reference,
)


def _make_entity(
    *,
    name: str,
    entity_type: str = "PC",
    user_id: str | None = "player-1",
    present: bool = True,
    sheet: dict | None = None,
) -> CampaignEntity:
    entity_id = uuid.uuid4()
    resolved_sheet = sheet or Dnd5ePlugin().default_pc_sheet()
    document: dict = {
        "identity": {"name": name},
        "system_mechanics": {
            "system_id": "dnd5e",
            "schema_version": "1.0.0",
            "sheet": resolved_sheet,
        },
        "state_flags": {"is_present_in_scene": present, "is_incapacitated": False},
    }
    if entity_type == "PC" and user_id is not None:
        document["player_binding"] = {"user_id": user_id}
    if entity_type == "NPC":
        document["state_flags"] = {"is_dead": False, "is_present_in_scene": True}

    entity = CampaignEntity(
        id=entity_id,
        campaign_id=uuid.uuid4(),
        entity_type=entity_type,
        document=document,
    )
    return entity


class TestCombatPluginGate:
    def test_dnd5e_supported(self):
        plugin = get_combat_plugin("dnd5e")
        assert plugin.system_id == "dnd5e"

    def test_generic_rejected(self):
        with pytest.raises(CombatResolverError, match="not supported"):
            get_combat_plugin(None)

    def test_cyberpunk_supported(self):
        from app.rules.cyberpunk_red.plugin import CyberpunkRedPlugin

        plugin = get_combat_plugin("cyberpunk_red")
        assert isinstance(plugin, CyberpunkRedPlugin)

    def test_vtm_rejected(self):
        with pytest.raises(CombatResolverError, match="not supported"):
            get_combat_plugin("vtm_v5")


class TestEntityResolution:
    def test_resolve_by_exact_name(self):
        goblin = _make_entity(name="Goblin Skulk", entity_type="NPC", user_id=None)
        kaelen = _make_entity(name="Kaelen Vorr")
        resolved = resolve_entity_reference("Goblin Skulk", [goblin, kaelen])
        assert resolved.id == goblin.id

    def test_resolve_by_case_insensitive_name(self):
        arturo = _make_entity(name="Arturo")
        resolved = resolve_entity_reference("arturo", [arturo])
        assert resolved.id == arturo.id

    def test_resolve_by_partial_unique_name(self):
        goblin = _make_entity(name="Goblin Skulk", entity_type="NPC", user_id=None)
        kaelen = _make_entity(name="Kaelen Vorr")
        resolved = resolve_entity_reference("goblin", [goblin, kaelen])
        assert resolved.id == goblin.id

    def test_ambiguous_name_raises(self):
        first = _make_entity(name="Goblin Alpha", entity_type="NPC", user_id=None)
        second = _make_entity(name="Goblin Beta", entity_type="NPC", user_id=None)
        with pytest.raises(CombatResolverError, match="Ambiguous"):
            resolve_entity_reference("goblin", [first, second])

    def test_missing_entity_raises(self):
        with pytest.raises(CombatResolverError, match="No entity"):
            resolve_entity_reference("ghost", [])


class TestSceneCombatEntities:
    def test_includes_pcs_without_present_flag_when_no_initiative(self):
        norman = _make_entity(name="Norman", present=False)
        arturo = _make_entity(name="Arturo", present=False, user_id="player-2")

        db = AsyncMock()
        db.scalars = AsyncMock(
            return_value=MagicMock(all=lambda: [norman, arturo]),
        )

        campaign_id = uuid.uuid4()
        state = SceneState(
            metadata=SceneMetadata(campaign_id=str(campaign_id), status="ACTIVE"),
            context=SceneContext(active_npc_ids=[]),
            state_flags=StateFlags(),
        )

        entities = asyncio.run(fetch_scene_combat_entities(db, campaign_id, state))
        names = {entity_display_name(entity) for entity in entities}
        assert names == {"Norman", "Arturo"}


class TestPermissions:
    def test_master_can_use_npc_attacker(self):
        npc = _make_entity(name="Goblin", entity_type="NPC", user_id=None)
        assert_attacker_permission(npc, sender_id="someone-else", sender_role="MASTER")

    def test_player_can_use_own_pc(self):
        pc = _make_entity(name="Kaelen", user_id="player-1")
        assert_attacker_permission(pc, sender_id="player-1", sender_role="PLAYER")

    def test_player_cannot_use_npc(self):
        npc = _make_entity(name="Goblin", entity_type="NPC", user_id=None)
        with pytest.raises(CombatResolverError, match="own character"):
            assert_attacker_permission(npc, sender_id="player-1", sender_role="PLAYER")

    def test_player_cannot_use_other_pc(self):
        pc = _make_entity(name="Mara", user_id="player-2")
        with pytest.raises(CombatResolverError, match="own character"):
            assert_attacker_permission(pc, sender_id="player-1", sender_role="PLAYER")


def _fake_randint(a: int, b: int) -> int:
    if b == 20:
        return 16
    if b == 8:
        return 5
    if b == 6:
        return 4
    return 4


class TestExecuteAttack:
    def test_attack_updates_defender_hp_and_emits_messages(self, monkeypatch):
        monkeypatch.setattr("random.randint", _fake_randint)

        attacker = _make_entity(name="Kaelen Vorr")
        defender = _make_entity(
            name="Goblin Skulk",
            entity_type="NPC",
            user_id=None,
            sheet=Dnd5ePlugin().default_npc_sheet("medium"),
        )
        entities = [attacker, defender]

        db = AsyncMock()
        db.scalars = AsyncMock(
            side_effect=[
                MagicMock(all=lambda: [entity for entity in entities if entity.entity_type == "PC"]),
                MagicMock(all=lambda: [defender]),
                MagicMock(all=lambda: []),
            ]
        )
        db.scalar = AsyncMock(return_value=None)

        campaign = Campaign(id=uuid.uuid4(), name="Test", game_system="dnd5e")
        state = SceneState(
            metadata=SceneMetadata(campaign_id=str(campaign.id), status="ACTIVE"),
            context=SceneContext(active_npc_ids=[str(defender.id)]),
            state_flags=StateFlags(),
        )

        result = asyncio.run(
            execute_attack(
                db,
                campaign,
                state,
                sender_id="player-1",
                sender_role="PLAYER",
                attacker_ref="Kaelen",
                defender_ref="Goblin",
            )
        )

        assert defender.document["system_mechanics"]["sheet"]["hp"]["current"] == 8
        assert len(result.messages) == 1
        combat = result.messages[0]
        assert combat["type"] == "COMBAT"
        assert combat["combat_event"]["kind"] == "ATTACK_RESOLVED"
        assert combat["combat_event"]["attack_roll"]["hit"] is True
        assert combat["combat_event"]["attacker_name"] == entity_display_name(attacker)
        assert combat["combat_event"]["defender_name"] == entity_display_name(defender)
        assert combat["combat_event"]["attack_roll"]["target_ac"] is not None
        assert "modifier" in combat["combat_event"]["attack_roll"]
        assert combat["combat_event"]["attack_roll"]["rolls"]
        assert "vs CA" in combat["combat_event"]["attack_roll"]["chat_summary"]
        assert "1d8=" in combat["combat_event"]["damage"]["chat_summary"]
        assert entity_display_name(attacker) in combat["text"]
        assert "1d20" in combat["chat_summary"]
