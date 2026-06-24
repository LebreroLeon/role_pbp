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
    execute_initiative,
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


class TestExecuteSaveAttack:
    def test_save_fail_rolls_damage_and_updates_chat(self, monkeypatch):
        monkeypatch.setattr("random.randint", lambda a, b: 5 if b == 20 else (6 if b == 8 else 4))

        save_sheet = {
            "proficiency_bonus": 3,
            "abilities": {"str": 10, "dex": 10, "con": 10, "int": 18, "wis": 10, "cha": 10},
            "spellcasting": {"ability": "int", "save_dc": 16},
            "ac": 12,
            "hp": {"max": 40, "current": 40},
            "attacks": [
                {
                    "name": "Bola de fuego",
                    "damage_dice": "8d6",
                    "damage_type": "fuego",
                    "effect_type": "damage",
                    "resolution": "save",
                    "save_ability": "dex",
                    "half_damage_on_save": True,
                    "to_hit_bonus": 0,
                }
            ],
        }
        attacker = _make_entity(name="Mago", sheet=save_sheet)
        defender = _make_entity(
            name="Goblin Skulk",
            entity_type="NPC",
            user_id=None,
            sheet={
                "ac": 12,
                "hp": {"max": 40, "current": 40},
                "abilities": {"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10},
                "proficiency_bonus": 2,
                "saving_throws": [],
            },
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
                sender_role="MASTER",
                attacker_ref="Mago",
                defender_ref="Goblin",
                weapon_name="Bola de fuego",
                attack_index=0,
            )
        )

        assert defender.document["system_mechanics"]["sheet"]["hp"]["current"] == 8
        combat = result.messages[0]["combat_event"]
        assert combat["attack_roll"]["resolution"] == "save"
        assert combat["damage"]["amount"] == 32
        assert "fuego" in result.messages[0]["chat_summary"]
        assert "= 32" in result.messages[0]["chat_summary"]

    def test_save_without_damage_dice_emits_only_save_result(self, monkeypatch):
        monkeypatch.setattr("random.randint", lambda a, b: 18 if b == 20 else 4)

        save_sheet = {
            "proficiency_bonus": 3,
            "abilities": {"str": 10, "dex": 10, "con": 10, "int": 18, "wis": 10, "cha": 10},
            "spellcasting": {"ability": "int", "save_dc": 16},
            "ac": 12,
            "hp": {"max": 40, "current": 40},
            "attacks": [
                {
                    "name": "Sugerencia",
                    "damage_dice": "",
                    "damage_type": "psiquico",
                    "effect_type": "damage",
                    "resolution": "save",
                    "save_ability": "wis",
                    "half_damage_on_save": False,
                    "to_hit_bonus": 0,
                }
            ],
        }
        attacker = _make_entity(name="Mago", sheet=save_sheet)
        defender = _make_entity(
            name="Goblin Skulk",
            entity_type="NPC",
            user_id=None,
            sheet={
                "ac": 12,
                "hp": {"max": 40, "current": 40},
                "abilities": {"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10},
                "proficiency_bonus": 2,
                "saving_throws": [],
            },
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
                sender_role="MASTER",
                attacker_ref="Mago",
                defender_ref="Goblin",
                weapon_name="Sugerencia",
                attack_index=0,
            )
        )

        assert defender.document["system_mechanics"]["sheet"]["hp"]["current"] == 40
        combat = result.messages[0]["combat_event"]
        assert combat["attack_roll"]["resolution"] == "save"
        assert "damage" not in combat
        assert "no le afecta" in result.messages[0]["chat_summary"]
        assert "Daño" not in result.messages[0]["chat_summary"]
        assert "pierde" not in result.messages[0]["chat_summary"]


class TestSaveAttackHpPersistence:
    def test_save_fail_persists_hp_and_initiative_sync(self, monkeypatch):
        monkeypatch.setattr("random.randint", lambda a, b: 7 if b == 20 else 1)

        caster_sheet = {
            "proficiency_bonus": 2,
            "abilities": {"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 14, "cha": 10},
            "spellcasting": {"ability": "wis", "save_dc": 11},
            "ac": 12,
            "hp": {"max": 20, "current": 20},
            "attacks": [
                {
                    "name": "Cosas Frias",
                    "damage_dice": "1d4",
                    "damage_type": "frio",
                    "effect_type": "damage",
                    "resolution": "save",
                    "save_ability": "wis",
                    "half_damage_on_save": False,
                    "to_hit_bonus": 0,
                }
            ],
        }
        attacker = _make_entity(name="Niolez", sheet=caster_sheet)
        defender = _make_entity(
            name="Glavenus",
            entity_type="NPC",
            user_id=None,
            sheet={
                "ac": 14,
                "hp": {"max": 10, "current": 4},
                "abilities": {"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10},
                "proficiency_bonus": 2,
                "saving_throws": [],
            },
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
        from app.schemas.scene import InitiativeEntry

        state.combat.initiative_order = [
            InitiativeEntry(entity_id=str(defender.id), entity_type="NPC", display_name="Glavenus")
        ]

        result = asyncio.run(
            execute_attack(
                db,
                campaign,
                state,
                sender_id="player-1",
                sender_role="MASTER",
                attacker_ref="Niolez",
                defender_ref="Glavenus",
                weapon_name="Cosas Frias",
                attack_index=0,
            )
        )

        sheet = defender.document["system_mechanics"]["sheet"]
        assert sheet["hp"]["current"] == 3
        assert result.modified_entities == [defender]
        initiative = state.combat.initiative_order[0]
        assert initiative.hp_current == 3
        assert initiative.hp_max == 10
        combat = result.messages[0]
        assert "PV 4 → 3" in combat["text"]
        assert "sufre el efecto completo" in combat["text"]
        assert "1d4=1 = 1" in combat["text"]
        assert "frío" in combat["text"]
        assert combat["combat_event"]["hp"]["after"] == 3

    def test_save_attack_applies_resistance_in_chat(self, monkeypatch):
        monkeypatch.setattr("random.randint", lambda a, b: 7 if b == 20 else 1)

        caster_sheet = {
            "proficiency_bonus": 2,
            "abilities": {"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 14, "cha": 10},
            "spellcasting": {"ability": "wis", "save_dc": 11},
            "ac": 12,
            "hp": {"max": 20, "current": 20},
            "attacks": [
                {
                    "name": "Chispa",
                    "damage_dice": "1d4",
                    "damage_type": "fuego",
                    "effect_type": "damage",
                    "resolution": "save",
                    "save_ability": "wis",
                    "half_damage_on_save": False,
                    "to_hit_bonus": 0,
                }
            ],
        }
        attacker = _make_entity(name="Piromante", sheet=caster_sheet)
        defender = _make_entity(
            name="Salamandra",
            entity_type="NPC",
            user_id=None,
            sheet={
                "ac": 14,
                "hp": {"max": 20, "current": 20},
                "abilities": {"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10},
                "proficiency_bonus": 2,
                "saving_throws": [],
                "damage_modifiers": {"resistances": ["fuego"], "vulnerabilities": [], "immunities": []},
            },
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
                sender_role="MASTER",
                attacker_ref="Piromante",
                defender_ref="Salamandra",
                weapon_name="Chispa",
                attack_index=0,
            )
        )

        assert defender.document["system_mechanics"]["sheet"]["hp"]["current"] == 20
        combat = result.messages[0]
        assert "resistencia" in combat["text"]
        assert combat["combat_event"]["damage"]["modified_amount"] == 0
        assert combat["combat_event"]["damage"]["raw_amount"] == 1


class TestExecuteInitiative:
    def test_rolls_only_track_entities_and_sorts_descending(self, monkeypatch):
        monkeypatch.setattr("random.randint", lambda _a, _b: 10)

        fast = _make_entity(name="Rápido", user_id="player-1")
        slow = _make_entity(name="Lento", user_id="player-2")
        off_track = _make_entity(name="Fuera", user_id="player-3", present=False)

        db = AsyncMock()
        db.scalar = AsyncMock(return_value=None)
        db.scalars = AsyncMock(return_value=MagicMock(all=lambda: []))

        campaign = Campaign(id=uuid.uuid4(), name="Test", game_system="dnd5e")
        state = SceneState(
            metadata=SceneMetadata(campaign_id=str(campaign.id), status="ACTIVE"),
            context=SceneContext(active_npc_ids=[]),
            state_flags=StateFlags(),
        )

        track_ids = [str(fast.id), str(slow.id)]

        def fake_fetch_entities_by_id(_db, _campaign_id, entity_ids):
            by_id = {str(fast.id): fast, str(slow.id): slow, str(off_track.id): off_track}
            return {entity_id: by_id[entity_id] for entity_id in entity_ids if entity_id in by_id}

        monkeypatch.setattr(
            "app.services.pbp_turn.fetch_entities_by_id",
            AsyncMock(side_effect=fake_fetch_entities_by_id),
        )

        result = asyncio.run(
            execute_initiative(
                db,
                campaign,
                state,
                sender_id="master-1",
                sender_role="MASTER",
                activate_combat=False,
                entity_ids=track_ids,
            )
        )

        rolled_ids = [entry.entity_id for entry in state.combat.initiative_order]
        assert rolled_ids == track_ids
        assert off_track.id not in {uuid.UUID(entity_id) for entity_id in rolled_ids}
        assert state.combat.is_active is False
        assert result.messages[0]["combat_event"]["kind"] == "INITIATIVE_ROLLED"
