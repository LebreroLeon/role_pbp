import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.campaign import Scene
from app.schemas.scene import ChatMessage, SceneContext, SceneMetadata, SceneState, TurnManagement
from app.services.unread_counts import count_play_unread, get_unread_counts


def _make_scene_with_messages(messages: list[dict], *, status: str = "ACTIVE") -> Scene:
    campaign_id = uuid.uuid4()
    chat_buffer = [
        ChatMessage.model_validate(
            {
                "id": msg.get("id", str(uuid.uuid4())),
                "timestamp": msg.get("timestamp", "2026-01-01T00:00:00Z"),
                "sender_id": msg["sender_id"],
                "type": msg.get("type", "ACTION"),
                "text": msg.get("text", "hola"),
                "read_by": msg.get("read_by", []),
                "visibility": msg.get("visibility", "all"),
            },
        )
        for msg in messages
    ]
    state = SceneState(
        metadata=SceneMetadata(campaign_id=str(campaign_id), status=status),
        context=SceneContext(
            location_id=None,
            active_npc_ids=[],
            hidden_npc_ids=[],
            scene_objective=None,
        ),
        turn_management=TurnManagement(current_turn_player_id=None, turn_order=[]),
        chat_buffer=chat_buffer,
    )
    return Scene(
        id=uuid.uuid4(),
        campaign_id=campaign_id,
        scene_number=1,
        display_name=None,
        status=status,
        scene_state=state.model_dump(),
    )


class TestCountPlayUnread:
    def test_excludes_own_messages(self):
        user_id = "user-a"
        scene = _make_scene_with_messages(
            [
                {"sender_id": user_id, "read_by": [user_id]},
                {"sender_id": "user-b", "read_by": [user_id]},
            ],
        )
        assert count_play_unread(scene, user_id, viewer_role="PLAYER") == 0

    def test_counts_unread_from_others(self):
        user_id = "user-a"
        scene = _make_scene_with_messages(
            [
                {"sender_id": "user-b", "read_by": ["user-b"]},
                {"sender_id": "user-c", "read_by": ["user-c"]},
            ],
        )
        assert count_play_unread(scene, user_id, viewer_role="PLAYER") == 2

    def test_players_do_not_count_master_only(self):
        user_id = "user-a"
        scene = _make_scene_with_messages(
            [
                {"sender_id": "master", "read_by": [], "visibility": "master_only"},
                {"sender_id": "user-b", "read_by": [], "visibility": "all"},
            ],
        )
        assert count_play_unread(scene, user_id, viewer_role="PLAYER") == 1

    def test_master_sees_master_only_unread(self):
        user_id = "master"
        scene = _make_scene_with_messages(
            [
                {"sender_id": "user-b", "read_by": [], "visibility": "master_only"},
            ],
        )
        assert count_play_unread(scene, user_id, viewer_role="MASTER") == 1

    def test_closed_scene_returns_zero(self):
        scene = _make_scene_with_messages(
            [{"sender_id": "user-b", "read_by": []}],
            status="CLOSED",
        )
        assert count_play_unread(scene, "user-a", viewer_role="PLAYER") == 0


@pytest.mark.asyncio
async def test_get_unread_counts_combines_play_and_ooc():
    campaign_id = uuid.uuid4()
    user_id = uuid.uuid4()
    scene = _make_scene_with_messages([{"sender_id": "other", "read_by": []}])

    db = AsyncMock()
    db.scalar = AsyncMock(side_effect=[scene, None, 3])

    counts = await get_unread_counts(db, campaign_id, user_id, viewer_role="PLAYER")
    assert counts.play == 1
    assert counts.ooc == 3
