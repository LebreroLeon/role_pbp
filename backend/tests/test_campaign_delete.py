import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_current_user, get_db
from app.main import app
from app.models.user import User
from app.services.campaigns import CampaignServiceError, delete_campaign


def _make_user() -> User:
    return User(
        id=uuid.uuid4(),
        email="master@test.com",
        password_hash="hash",
        display_name="Master User",
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


@pytest.mark.asyncio
async def test_delete_campaign_route_returns_204(override_db):
    user = _make_user()
    campaign_id = uuid.uuid4()
    _override_user(user)

    with (
        patch("app.api.routes.campaigns_mgmt.require_campaign_master", new_callable=AsyncMock),
        patch("app.api.routes.campaigns_mgmt.delete_campaign", new_callable=AsyncMock) as delete_service,
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete(f"/api/v1/campaigns/{campaign_id}")

    assert response.status_code == 204
    delete_service.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_campaign_route_returns_404_when_missing(override_db):
    user = _make_user()
    campaign_id = uuid.uuid4()
    _override_user(user)

    with (
        patch("app.api.routes.campaigns_mgmt.require_campaign_master", new_callable=AsyncMock),
        patch(
            "app.api.routes.campaigns_mgmt.delete_campaign",
            new_callable=AsyncMock,
            side_effect=CampaignServiceError("Campaign not found"),
        ),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete(f"/api/v1/campaigns/{campaign_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Campaign not found"


@pytest.mark.asyncio
async def test_delete_campaign_service_removes_related_rows():
    campaign_id = uuid.uuid4()
    db = AsyncMock()
    campaign = object()
    db.scalar = AsyncMock(return_value=campaign)
    docs_result = MagicMock()
    docs_result.all.return_value = []
    db.scalars = AsyncMock(return_value=docs_result)
    db.execute = AsyncMock()
    db.delete = AsyncMock()
    db.commit = AsyncMock()

    with (
        patch("app.services.campaigns.get_storage_backend") as storage_factory,
        patch("app.services.campaigns.rag_service.purge_semantic_cache", new_callable=AsyncMock) as purge_cache,
    ):
        storage_factory.return_value.exists.return_value = False
        await delete_campaign(db, campaign_id)

    assert db.execute.await_count == 3
    db.delete.assert_awaited_once_with(campaign)
    db.commit.assert_awaited_once()
    purge_cache.assert_awaited_once_with(db, campaign_id=str(campaign_id))
