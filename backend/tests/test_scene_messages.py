import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.campaign import Scene, SceneMessage
from app.models.user import User
from app.schemas.scene import ChatMessage, SceneContext, SceneMetadata, SceneState, TurnManagement
from app.services.scene_messages import (
    list_all_scene_messages,
    list_scene_messages,
    persist_scene_message,
    scene_has_older_messages,
)
from app.services.scenes import append_chat_message, generate_scene_closure_summary, load_scene_state


def _make_scene(*, max_buffer: int = 3) -> Scene:
    campaign_id = uuid.uuid4()
    return Scene(
        id=uuid.uuid4(),
        campaign_id=campaign_id,
        scene_number=1,
        display_name="Test",
        status="ACTIVE",
        scene_state={
            "metadata": {"campaign_id": str(campaign_id), "status": "ACTIVE"},
            "context": {"location_id": None, "active_npc_ids": [], "hidden_npc_ids": [], "scene_objective": None},
            "turn_management": {"current_turn_player_id": None, "turn_order": []},
            "memory_settings": {
                "max_chat_buffer_size": max_buffer,
                "rag_top_k_matches": 3,
                "max_player_lore_queries_per_scene": 3,
            },
            "chat_buffer": [],
            "state_flags": {
                "conflict_mode_active": False,
                "ai_alert_triggered": False,
                "remaining_player_lore_tokens": 3,
            },
            "combat": {
                "is_active": False,
                "round": 0,
                "initiative_order": [],
                "current_turn_entity_id": None,
                "conflict_mode_active": False,
            },
        },
    )


def _message(message_id: str, text: str, *, index: int) -> dict:
    return {
        "id": message_id,
        "timestamp": f"2026-01-01T12:{index:02d}:00Z",
        "sender_id": str(uuid.uuid4()),
        "type": "ACTION",
        "text": text,
        "read_by": [],
    }


class TestAppendChatMessage:
    @pytest.mark.asyncio
    async def test_persists_messages_and_trims_buffer_only(self):
        scene = _make_scene(max_buffer=2)
        state = load_scene_state(scene)
        db = AsyncMock()
        db.get = AsyncMock(return_value=None)
        db.add = MagicMock()

        await append_chat_message(db, scene, state, _message("m1", "Uno", index=1))
        await append_chat_message(db, scene, state, _message("m2", "Dos", index=2))
        await append_chat_message(db, scene, state, _message("m3", "Tres", index=3))

        assert len(state.chat_buffer) == 2
        assert state.chat_buffer[0].id == "m2"
        assert state.chat_buffer[1].id == "m3"
        assert db.add.call_count == 3


class TestListSceneMessages:
    @pytest.mark.asyncio
    async def test_returns_older_messages_before_cursor(self):
        scene_id = uuid.uuid4()
        rows = [
            SceneMessage(
                id="m1",
                scene_id=scene_id,
                payload=_message("m1", "Uno", index=1),
                created_at=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
            ),
            SceneMessage(
                id="m2",
                scene_id=scene_id,
                payload=_message("m2", "Dos", index=2),
                created_at=datetime(2026, 1, 1, 12, 1, tzinfo=timezone.utc),
            ),
            SceneMessage(
                id="m3",
                scene_id=scene_id,
                payload=_message("m3", "Tres", index=3),
                created_at=datetime(2026, 1, 1, 12, 2, tzinfo=timezone.utc),
            ),
        ]

        db = AsyncMock()
        db.get = AsyncMock(return_value=rows[2])
        db.scalars = AsyncMock(return_value=MagicMock(all=MagicMock(return_value=[rows[1], rows[0]])))

        with patch(
            "app.services.scene_messages.fetch_likes_by_message_id",
            new=AsyncMock(return_value={}),
        ):
            messages = await list_scene_messages(db, scene_id, before_message_id="m3", limit=50)

        assert [message.id for message in messages] == ["m1", "m2"]

    @pytest.mark.asyncio
    async def test_hides_master_only_messages_from_players(self):
        scene_id = uuid.uuid4()
        rows = [
            SceneMessage(
                id="public",
                scene_id=scene_id,
                payload={
                    **_message("public", "Visible", index=1),
                    "visibility": "all",
                },
                created_at=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
            ),
            SceneMessage(
                id="secret",
                scene_id=scene_id,
                payload={
                    **_message("secret", "Oculto", index=2),
                    "visibility": "master_only",
                },
                created_at=datetime(2026, 1, 1, 12, 1, tzinfo=timezone.utc),
            ),
        ]

        db = AsyncMock()
        db.scalars = AsyncMock(return_value=MagicMock(all=MagicMock(return_value=rows)))

        with patch(
            "app.services.scene_messages.fetch_likes_by_message_id",
            new=AsyncMock(return_value={}),
        ):
            player_messages = await list_scene_messages(db, scene_id, viewer_role="PLAYER")
            master_messages = await list_scene_messages(db, scene_id, viewer_role="MASTER")

        assert [message.id for message in player_messages] == ["public"]
        assert [message.id for message in master_messages] == ["public", "secret"]

    @pytest.mark.asyncio
    async def test_scene_has_older_messages_before_cursor(self):
        scene_id = uuid.uuid4()
        rows = [
            SceneMessage(
                id="m1",
                scene_id=scene_id,
                payload=_message("m1", "Uno", index=1),
                created_at=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
            ),
            SceneMessage(
                id="m2",
                scene_id=scene_id,
                payload=_message("m2", "Dos", index=2),
                created_at=datetime(2026, 1, 1, 12, 1, tzinfo=timezone.utc),
            ),
            SceneMessage(
                id="m3",
                scene_id=scene_id,
                payload=_message("m3", "Tres", index=3),
                created_at=datetime(2026, 1, 1, 12, 2, tzinfo=timezone.utc),
            ),
        ]

        db = AsyncMock()
        db.get = AsyncMock(return_value=rows[1])
        db.scalar = AsyncMock(return_value=1)

        has_older = await scene_has_older_messages(
            db,
            scene_id,
            oldest_visible_message_id="m2",
        )

        assert has_older is True

    @pytest.mark.asyncio
    async def test_scene_has_older_messages_false_when_oldest_visible(self):
        scene_id = uuid.uuid4()
        oldest = SceneMessage(
            id="m1",
            scene_id=scene_id,
            payload=_message("m1", "Uno", index=1),
            created_at=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
        )

        db = AsyncMock()
        db.get = AsyncMock(return_value=oldest)
        db.scalar = AsyncMock(return_value=0)

        has_older = await scene_has_older_messages(
            db,
            scene_id,
            oldest_visible_message_id="m1",
        )

        assert has_older is False

    @pytest.mark.asyncio
    async def test_uses_timestamp_when_before_message_missing_from_db(self):
        scene_id = uuid.uuid4()
        rows = [
            SceneMessage(
                id="m1",
                scene_id=scene_id,
                payload=_message("m1", "Antiguo", index=1),
                created_at=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
            ),
        ]

        db = AsyncMock()
        db.get = AsyncMock(return_value=None)
        db.scalars = AsyncMock(return_value=MagicMock(all=MagicMock(return_value=rows)))

        with patch(
            "app.services.scene_messages.fetch_likes_by_message_id",
            new=AsyncMock(return_value={}),
        ):
            messages = await list_scene_messages(
                db,
                scene_id,
                before_message_id="buffer-only",
                before_timestamp="2026-01-01T12:30:00Z",
                limit=50,
            )

        assert [message.id for message in messages] == ["m1"]

    @pytest.mark.asyncio
    async def test_scene_has_older_messages_uses_timestamp_fallback(self):
        scene_id = uuid.uuid4()
        db = AsyncMock()
        db.get = AsyncMock(return_value=None)
        db.scalar = AsyncMock(return_value=2)

        has_older = await scene_has_older_messages(
            db,
            scene_id,
            oldest_visible_message_id="buffer-only",
            oldest_visible_timestamp="2026-06-28T19:18:00Z",
        )

        assert has_older is True


class TestSceneClosureSummary:
    @pytest.mark.asyncio
    async def test_uses_full_persisted_history_not_trimmed_buffer(self):
        state = SceneState(
            metadata=SceneMetadata(campaign_id=str(uuid.uuid4()), status="ACTIVE"),
            context=SceneContext(),
            turn_management=TurnManagement(),
            chat_buffer=[
                ChatMessage.model_validate(_message("m2", "Reciente", index=2)),
            ],
        )
        scene_id = uuid.uuid4()
        db = AsyncMock()
        db.scalars = AsyncMock(
            return_value=MagicMock(
                all=MagicMock(
                    return_value=[
                        SceneMessage(
                            id="m1",
                            scene_id=scene_id,
                            payload=_message("m1", "Antiguo", index=1),
                            created_at=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
                        ),
                        SceneMessage(
                            id="m2",
                            scene_id=scene_id,
                            payload=_message("m2", "Reciente", index=2),
                            created_at=datetime(2026, 1, 1, 12, 1, tzinfo=timezone.utc),
                        ),
                    ]
                )
            )
        )

        from app.services.llm import LLMNotConfiguredError

        with patch(
            "app.services.scenes.chat_completion",
            new=AsyncMock(side_effect=LLMNotConfiguredError("no key")),
        ):
            summary = await generate_scene_closure_summary(
                state,
                scene_number=1,
                display_name=None,
                db=db,
                scene_id=scene_id,
            )

        assert "Antiguo" in summary
        assert "Reciente" in summary


def _make_user() -> User:
    return User(
        id=uuid.uuid4(),
        email="player@example.com",
        password_hash="hash",
        display_name="Player One",
    )


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def override_db(mock_db):
    from app.core.database import get_db

    async def _override():
        yield mock_db

    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.clear()


def _override_user(user: User):
    from app.api.deps import get_current_user

    async def _override():
        return user

    app.dependency_overrides[get_current_user] = _override


@pytest.mark.asyncio
async def test_list_scene_messages_route(override_db, mock_db):
    user = _make_user()
    scene_id = uuid.uuid4()
    _override_user(user)

    message = ChatMessage.model_validate(_message("m1", "Hola", index=1))

    with (
        patch("app.api.routes.scenes.get_scene_for_member", new=AsyncMock(return_value=MagicMock(id=scene_id))),
        patch("app.api.routes.scenes.require_player_open_scene", new=AsyncMock()),
        patch("app.api.routes.scenes.require_campaign_member", new=AsyncMock(return_value="PLAYER")),
        patch(
            "app.api.routes.scenes.list_scene_messages",
            new=AsyncMock(return_value=[message]),
        ) as list_messages,
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/api/v1/scenes/{scene_id}/messages?before=m2&limit=25")

    assert response.status_code == 200
    assert response.json()[0]["id"] == "m1"
    list_messages.assert_awaited_once()


@pytest.mark.asyncio
async def test_scene_messages_has_older_route(override_db, mock_db):
    user = _make_user()
    scene_id = uuid.uuid4()
    _override_user(user)

    with (
        patch("app.api.routes.scenes.get_scene_for_member", new=AsyncMock(return_value=MagicMock(id=scene_id))),
        patch("app.api.routes.scenes.require_player_open_scene", new=AsyncMock()),
        patch("app.api.routes.scenes.require_campaign_member", new=AsyncMock(return_value="PLAYER")),
        patch(
            "app.api.routes.scenes.scene_has_older_messages",
            new=AsyncMock(return_value=True),
        ) as has_older,
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/scenes/{scene_id}/messages/has-older?before=m2&before_timestamp=2026-06-28T19:18:00Z",
            )

    assert response.status_code == 200
    assert response.json() == {"has_older": True}
    has_older.assert_awaited_once()
