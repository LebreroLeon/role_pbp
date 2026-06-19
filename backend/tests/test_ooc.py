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
