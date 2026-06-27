import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.campaign import Campaign, CampaignEntity
from app.rules.base import DamageResult
from app.rules.dnd5e.plugin import Dnd5ePlugin
from app.schemas.scene import SceneContext, SceneMetadata, SceneState, StateFlags
from app.services.combat_resolver import _damage_flag_updates, execute_attack
from app.rules.base import DamageApplication


def _make_entity(
    *,
    name: str,
    entity_type: str = "PC",
    user_id: str | None = "player-1",
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
        "state_flags": {"is_present_in_scene": True, "is_incapacitated": True},
    }
    if entity_type == "PC" and user_id is not None:
        document["player_binding"] = {"user_id": user_id}

    return CampaignEntity(
        id=entity_id,
        campaign_id=uuid.uuid4(),
        entity_type=entity_type,
        document=document,
    )


def _fake_randint(a: int, b: int) -> int:
    if b == 8:
        return 6
    return 10


class TestHealingCombatFlow:
    def test_healing_attack_updates_defender_and_chat(self, monkeypatch):
        monkeypatch.setattr("random.randint", _fake_randint)

        cleric_sheet = {
            "attacks": [
                {
                    "name": "Curar heridas",
                    "to_hit_bonus": 0,
                    "damage_dice": "1d8+3",
                    "damage_type": "radiante",
                    "effect_type": "healing",
                }
            ]
        }
        fighter_sheet = {"hp": {"max": 24, "current": 10, "temp": 0}, "ac": 16}

        cleric = _make_entity(name="Elara", sheet=cleric_sheet)
        fighter = _make_entity(name="Kaelen", user_id="player-2", sheet=fighter_sheet)
        entities = [cleric, fighter]

        db = AsyncMock()
        db.scalars = AsyncMock(
            side_effect=[
                MagicMock(all=lambda: [entity for entity in entities if entity.entity_type == "PC"]),
                MagicMock(all=lambda: []),
                MagicMock(all=lambda: []),
            ]
        )
        db.scalar = AsyncMock(return_value=None)

        campaign = Campaign(id=uuid.uuid4(), name="Test", game_system="dnd5e")
        state = SceneState(
            metadata=SceneMetadata(campaign_id=str(campaign.id), status="ACTIVE"),
            context=SceneContext(active_npc_ids=[]),
            state_flags=StateFlags(),
        )

        result = asyncio.run(
            execute_attack(
                db,
                campaign,
                state,
                sender_id="player-1",
                sender_role="MASTER",
                attacker_ref="Elara",
                defender_ref="Kaelen",
                weapon_name="Curar heridas",
            )
        )

        updated_hp = fighter.document["system_mechanics"]["sheet"]["hp"]["current"]
        assert updated_hp == 19
        assert fighter.document["state_flags"]["is_incapacitated"] is False

        combat = result.messages[0]
        assert combat["type"] == "COMBAT"
        assert "cura a" in combat["text"]
        assert "Curación" in combat["text"]
        assert combat["combat_event"]["damage"]["is_healing"] is True
        assert "Daño" not in combat["combat_event"]["damage"]["chat_summary"]

    def test_healing_capped_at_max_hp(self):
        plugin = Dnd5ePlugin()
        defender = {"hp": {"max": 20, "current": 19, "temp": 0}}
        updated, application = plugin.apply_damage(
            defender,
            DamageResult(
                amount=8,
                expression="1d8+3",
                rolls=[6],
                damage_type="radiante",
                is_healing=True,
            ),
        )
        assert application.amount_applied == 1
        assert updated["hp"]["current"] == 20

    def test_healing_clears_ko_flags_for_npc(self):
        npc = _make_entity(
            name="Glavenus",
            entity_type="NPC",
            user_id=None,
            sheet={"hp": {"max": 30, "current": 0, "temp": 0}, "ac": 15},
        )
        npc.document["state_flags"] = {
            "is_present_in_scene": True,
            "is_incapacitated": True,
            "is_dead": True,
        }

        flags = _damage_flag_updates(
            npc,
            DamageApplication(
                damage_dealt=10,
                damage_type="radiante",
                hp_before=0,
                hp_after=10,
                is_healing=True,
            ),
        )

        assert flags["is_incapacitated"] is False
        assert flags["is_dead"] is False
