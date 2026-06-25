import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_current_user, get_db
from app.main import app
from app.models.user import User
from app.schemas.ooc import OocMessageResponse
from app.services.campaign_ws import user_can_see_ooc_message
from app.services.ooc import (
    OOC_CHANNEL_ALL,
    OOC_CHANNEL_MASTER,
    message_matches_ooc_channel,
    normalize_ooc_channel,
)


def _make_user() -> User:
    return User(
        id=uuid.uuid4(),
        email="user@test.com",
        password_hash="hash",
        display_name="Test User",
    )


def _make_message(
    *,
    author_id: uuid.UUID,
    campaign_id: uuid.UUID,
    message_type: str = "OOC_PUBLIC",
    target_id: uuid.UUID | None = None,
) -> OocMessageResponse:
    return OocMessageResponse(
        id=str(uuid.uuid4()),
        campaign_id=str(campaign_id),
        author_user_id=str(author_id),
        author_display_name="Test User",
        content="Hello OOC",
        message_type=message_type,
        target_user_id=str(target_id) if target_id else None,
        target_display_name="Target User" if target_id else None,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def override_db(mock_db):
    async def _get_db():
        yield mock_db

    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.pop(get_db, None)


def _override_user(user: User):
    async def _get_current_user():
        return user

    app.dependency_overrides[get_current_user] = _get_current_user


def test_whisper_visibility_only_for_participants():
    author = str(uuid.uuid4())
    target = str(uuid.uuid4())
    outsider = str(uuid.uuid4())

    assert user_can_see_ooc_message("OOC_WHISPER", author, target, author)
    assert user_can_see_ooc_message("OOC_WHISPER", author, target, target)
    assert not user_can_see_ooc_message("OOC_WHISPER", author, target, outsider)


def test_public_message_visible_to_everyone():
    author = str(uuid.uuid4())
    viewer = str(uuid.uuid4())
    assert user_can_see_ooc_message("OOC_PUBLIC", author, None, viewer)


@pytest.mark.asyncio
async def test_get_ooc_messages_requires_membership(override_db):
    user = _make_user()
    campaign_id = uuid.uuid4()
    _override_user(user)

    with patch("app.api.routes.ooc.require_campaign_member", new_callable=AsyncMock) as require_member:
        require_member.side_effect = Exception("should not reach service")
        from fastapi import HTTPException

        require_member.side_effect = HTTPException(status_code=404, detail="Campaign not found")

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/v1/campaigns/{campaign_id}/ooc/messages")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_post_ooc_public_message(override_db):
    user = _make_user()
    campaign_id = uuid.uuid4()
    _override_user(user)
    message = _make_message(author_id=user.id, campaign_id=campaign_id)

    with (
        patch("app.api.routes.ooc.require_campaign_member", new_callable=AsyncMock, return_value="PLAYER"),
        patch("app.api.routes.ooc.post_ooc_public", new_callable=AsyncMock, return_value=message),
        patch("app.api.routes.ooc.campaign_ws_manager.broadcast_ooc_message", new_callable=AsyncMock) as broadcast,
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/campaigns/{campaign_id}/ooc/messages",
                json={"content": "Hello OOC"},
            )

    assert response.status_code == 201
    assert response.json()["content"] == "Hello OOC"
    broadcast.assert_awaited_once()


@pytest.mark.asyncio
async def test_post_ooc_whisper_message(override_db):
    user = _make_user()
    target_id = uuid.uuid4()
    campaign_id = uuid.uuid4()
    _override_user(user)
    message = _make_message(
        author_id=user.id,
        campaign_id=campaign_id,
        message_type="OOC_WHISPER",
        target_id=target_id,
    )

    with (
        patch("app.api.routes.ooc.require_campaign_member", new_callable=AsyncMock, return_value="MASTER"),
        patch("app.api.routes.ooc.create_ooc_whisper", new_callable=AsyncMock, return_value=message),
        patch("app.api.routes.ooc.campaign_ws_manager.broadcast_ooc_message", new_callable=AsyncMock) as broadcast,
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/campaigns/{campaign_id}/ooc/whispers",
                json={"content": "Secret", "target_user_id": str(target_id)},
            )

    assert response.status_code == 201
    assert response.json()["message_type"] == "OOC_WHISPER"
    broadcast.assert_awaited_once()


@pytest.mark.asyncio
async def test_post_ooc_whisper_passes_five_service_args(override_db, mock_db):
    user = _make_user()
    target_id = uuid.uuid4()
    campaign_id = uuid.uuid4()
    _override_user(user)
    message = _make_message(
        author_id=user.id,
        campaign_id=campaign_id,
        message_type="OOC_WHISPER",
        target_id=target_id,
    )

    with (
        patch("app.api.routes.ooc.require_campaign_member", new_callable=AsyncMock, return_value="MASTER"),
        patch("app.api.routes.ooc.create_ooc_whisper", new_callable=AsyncMock, return_value=message) as whisper,
        patch("app.api.routes.ooc.campaign_ws_manager.broadcast_ooc_message", new_callable=AsyncMock),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/campaigns/{campaign_id}/ooc/whispers",
                json={"content": "Secret", "target_user_id": str(target_id)},
            )

    assert response.status_code == 201
    whisper.assert_awaited_once_with(mock_db, campaign_id, user.id, target_id, "Secret")


def test_normalize_ooc_channel_defaults_to_none():
    assert normalize_ooc_channel(None) is None
    assert normalize_ooc_channel("") is None
    assert normalize_ooc_channel("  ALL  ") == OOC_CHANNEL_ALL


def test_message_matches_public_channel_only():
    author = str(uuid.uuid4())
    viewer = str(uuid.uuid4())
    assert message_matches_ooc_channel(
        message_type="OOC_PUBLIC",
        author_user_id=author,
        target_user_id=None,
        channel=OOC_CHANNEL_ALL,
        viewer_user_id=viewer,
        master_user_ids=set(),
    )
    assert not message_matches_ooc_channel(
        message_type="OOC_WHISPER",
        author_user_id=author,
        target_user_id=viewer,
        channel=OOC_CHANNEL_ALL,
        viewer_user_id=viewer,
        master_user_ids=set(),
    )


def test_message_matches_master_channel_for_player():
    player = str(uuid.uuid4())
    master = str(uuid.uuid4())
    outsider = str(uuid.uuid4())

    assert message_matches_ooc_channel(
        message_type="OOC_WHISPER",
        author_user_id=player,
        target_user_id=master,
        channel=OOC_CHANNEL_MASTER,
        viewer_user_id=player,
        master_user_ids={master},
    )
    assert message_matches_ooc_channel(
        message_type="OOC_WHISPER",
        author_user_id=master,
        target_user_id=player,
        channel=OOC_CHANNEL_MASTER,
        viewer_user_id=player,
        master_user_ids={master},
    )
    assert not message_matches_ooc_channel(
        message_type="OOC_WHISPER",
        author_user_id=player,
        target_user_id=outsider,
        channel=OOC_CHANNEL_MASTER,
        viewer_user_id=player,
        master_user_ids={master},
    )


def test_message_matches_player_channel_for_master():
    master = str(uuid.uuid4())
    player = str(uuid.uuid4())
    other_player = str(uuid.uuid4())

    assert message_matches_ooc_channel(
        message_type="OOC_WHISPER",
        author_user_id=master,
        target_user_id=player,
        channel=player,
        viewer_user_id=master,
        master_user_ids={master},
        player_user_id=player,
    )
    assert not message_matches_ooc_channel(
        message_type="OOC_WHISPER",
        author_user_id=master,
        target_user_id=other_player,
        channel=player,
        viewer_user_id=master,
        master_user_ids={master},
        player_user_id=player,
    )


@pytest.mark.asyncio
async def test_get_ooc_messages_passes_channel_filter(override_db, mock_db):
    user = _make_user()
    campaign_id = uuid.uuid4()
    _override_user(user)

    with (
        patch("app.api.routes.ooc.require_campaign_member", new_callable=AsyncMock, return_value="MASTER"),
        patch("app.api.routes.ooc.list_ooc_messages", new_callable=AsyncMock, return_value=[]) as list_messages,
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/campaigns/{campaign_id}/ooc/messages",
                params={"channel": "all"},
            )

    assert response.status_code == 200
    list_messages.assert_awaited_once_with(mock_db, campaign_id, user.id, channel="all")


@pytest.mark.asyncio
async def test_delete_ooc_message_requires_master(override_db):
    user = _make_user()
    campaign_id = uuid.uuid4()
    message_id = uuid.uuid4()
    _override_user(user)

    with patch("app.api.routes.ooc.require_campaign_master", new_callable=AsyncMock) as require_master:
        from fastapi import HTTPException

        require_master.side_effect = HTTPException(status_code=403, detail="Master role required")

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete(
                f"/api/v1/campaigns/{campaign_id}/ooc/messages/{message_id}",
            )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_ooc_message_broadcasts_and_returns_204(override_db, mock_db):
    user = _make_user()
    campaign_id = uuid.uuid4()
    message_id = uuid.uuid4()
    _override_user(user)
    deleted_payload = {
        "id": str(message_id),
        "message_type": "OOC_PUBLIC",
        "author_user_id": str(user.id),
        "target_user_id": None,
    }

    with (
        patch("app.api.routes.ooc.require_campaign_master", new_callable=AsyncMock, return_value="MASTER"),
        patch("app.api.routes.ooc.delete_ooc_message", new_callable=AsyncMock, return_value=deleted_payload) as delete,
        patch(
            "app.api.routes.ooc.campaign_ws_manager.broadcast_ooc_message_deleted",
            new_callable=AsyncMock,
        ) as broadcast_deleted,
        patch("app.api.routes.ooc.campaign_ws_manager.broadcast_unread_counts", new_callable=AsyncMock),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete(
                f"/api/v1/campaigns/{campaign_id}/ooc/messages/{message_id}",
            )

    assert response.status_code == 204
    delete.assert_awaited_once_with(mock_db, campaign_id, message_id)
    broadcast_deleted.assert_awaited_once_with(str(campaign_id), deleted_payload)
