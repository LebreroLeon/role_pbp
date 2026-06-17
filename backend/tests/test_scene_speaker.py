import asyncio
import uuid
from unittest.mock import AsyncMock

import pytest

from app.models.campaign import CampaignEntity, Scene
from app.rules.dnd5e.plugin import Dnd5ePlugin
from app.schemas.scene import PostMessageRequest
from app.services.scenes import (
    DEFAULT_NARRATOR_DISPLAY_NAME,
    SceneServiceError,
    resolve_message_speaker_fields,
)


def _make_scene(campaign_id: uuid.UUID | None = None) -> Scene:
    campaign_id = campaign_id or uuid.uuid4()
    return Scene(
        id=uuid.uuid4(),
        campaign_id=campaign_id,
        status="ACTIVE",
        scene_state={},
    )


def _make_entity(
    *,
    campaign_id: uuid.UUID,
    name: str,
    entity_type: str = "NPC",
) -> CampaignEntity:
    document: dict = {
        "identity": {"name": name},
        "system_mechanics": {
            "system_id": "dnd5e",
            "schema_version": "1.0.0",
            "sheet": Dnd5ePlugin().default_pc_sheet(),
        },
    }
    if entity_type == "PC":
        document["player_binding"] = {"user_id": str(uuid.uuid4())}
        document["state_flags"] = {"is_present_in_scene": True, "is_incapacitated": False}

    return CampaignEntity(
        id=uuid.uuid4(),
        campaign_id=campaign_id,
        entity_type=entity_type,
        document=document,
    )


class TestResolveMessageSpeakerFields:
    def test_master_defaults_to_narrator(self):
        scene = _make_scene()
        db = AsyncMock()

        result = asyncio.run(
            resolve_message_speaker_fields(
                db,
                scene,
                PostMessageRequest(type="ACTION", text="La puerta cruje."),
                sender_role="MASTER",
                msg_type="ACTION",
            )
        )

        assert result == {
            "speaker_type": "NARRATOR",
            "speaker_display_name": DEFAULT_NARRATOR_DISPLAY_NAME,
            "speaker_entity_id": None,
        }

    def test_master_can_impersonate_npc(self):
        scene = _make_scene()
        npc = _make_entity(campaign_id=scene.campaign_id, name="Goblin", entity_type="NPC")
        db = AsyncMock()
        db.scalar = AsyncMock(return_value=npc)

        result = asyncio.run(
            resolve_message_speaker_fields(
                db,
                scene,
                PostMessageRequest(
                    type="SPEAK",
                    text="¡Intrusos!",
                    speaker_type="NPC",
                    speaker_entity_id=str(npc.id),
                    speaker_display_name="Goblin",
                ),
                sender_role="MASTER",
                msg_type="SPEAK",
            )
        )

        assert result["speaker_type"] == "NPC"
        assert result["speaker_display_name"] == "Goblin"
        assert result["speaker_entity_id"] == str(npc.id)

    def test_master_can_impersonate_pc(self):
        scene = _make_scene()
        pc = _make_entity(campaign_id=scene.campaign_id, name="Kaelen", entity_type="PC")
        db = AsyncMock()
        db.scalar = AsyncMock(return_value=pc)

        result = asyncio.run(
            resolve_message_speaker_fields(
                db,
                scene,
                PostMessageRequest(
                    type="ACTION",
                    text="Empuja la puerta.",
                    speaker_type="PC",
                    speaker_entity_id=str(pc.id),
                ),
                sender_role="MASTER",
                msg_type="ACTION",
            )
        )

        assert result["speaker_type"] == "PC"
        assert result["speaker_display_name"] == "Kaelen"
        assert result["speaker_entity_id"] == str(pc.id)

    def test_player_cannot_set_speaker_identity(self):
        scene = _make_scene()
        db = AsyncMock()

        with pytest.raises(SceneServiceError, match="Only MASTER"):
            asyncio.run(
                resolve_message_speaker_fields(
                    db,
                    scene,
                    PostMessageRequest(
                        type="SPEAK",
                        text="Hola",
                        speaker_type="NPC",
                        speaker_entity_id=str(uuid.uuid4()),
                    ),
                    sender_role="PLAYER",
                    msg_type="SPEAK",
                )
            )

    def test_player_without_speaker_fields_returns_empty(self):
        scene = _make_scene()
        db = AsyncMock()

        result = asyncio.run(
            resolve_message_speaker_fields(
                db,
                scene,
                PostMessageRequest(type="SPEAK", text="Hola"),
                sender_role="PLAYER",
                msg_type="SPEAK",
            )
        )

        assert result == {}

    def test_unknown_entity_rejected(self):
        scene = _make_scene()
        db = AsyncMock()
        db.scalar = AsyncMock(return_value=None)

        with pytest.raises(SceneServiceError, match="not found"):
            asyncio.run(
                resolve_message_speaker_fields(
                    db,
                    scene,
                    PostMessageRequest(
                        type="SPEAK",
                        text="Hola",
                        speaker_type="NPC",
                        speaker_entity_id=str(uuid.uuid4()),
                    ),
                    sender_role="MASTER",
                    msg_type="SPEAK",
                )
            )

    def test_entity_type_mismatch_rejected(self):
        scene = _make_scene()
        pc = _make_entity(campaign_id=scene.campaign_id, name="Kaelen", entity_type="PC")
        db = AsyncMock()
        db.scalar = AsyncMock(return_value=pc)

        with pytest.raises(SceneServiceError, match="type mismatch"):
            asyncio.run(
                resolve_message_speaker_fields(
                    db,
                    scene,
                    PostMessageRequest(
                        type="SPEAK",
                        text="Hola",
                        speaker_type="NPC",
                        speaker_entity_id=str(pc.id),
                    ),
                    sender_role="MASTER",
                    msg_type="SPEAK",
                )
            )

    def test_speaker_not_allowed_on_dice_messages(self):
        scene = _make_scene()
        db = AsyncMock()

        with pytest.raises(SceneServiceError, match="not allowed"):
            asyncio.run(
                resolve_message_speaker_fields(
                    db,
                    scene,
                    PostMessageRequest(
                        type="DICE_ROLL",
                        text="1d20",
                        speaker_type="NPC",
                        speaker_entity_id=str(uuid.uuid4()),
                    ),
                    sender_role="MASTER",
                    msg_type="DICE_ROLL",
                )
            )
