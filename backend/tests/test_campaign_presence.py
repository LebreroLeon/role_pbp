import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.campaign_ws import CampaignConnectionManager


@pytest.fixture
def manager() -> CampaignConnectionManager:
    return CampaignConnectionManager()


def _socket(name: str) -> MagicMock:
    socket = MagicMock(name=name)
    socket.accept = AsyncMock()
    socket.send_json = AsyncMock()
    return socket


@pytest.mark.asyncio
async def test_get_online_user_ids_deduplicates_tabs(manager: CampaignConnectionManager) -> None:
    campaign_id = str(uuid.uuid4())
    user_id = uuid.uuid4()
    socket_a = _socket("a")
    socket_b = _socket("b")

    await manager.connect(campaign_id, socket_a, user_id)
    await manager.connect(campaign_id, socket_b, user_id)

    assert manager.get_online_user_ids(campaign_id) == [str(user_id)]


@pytest.mark.asyncio
async def test_disconnect_removes_user_when_last_socket_gone(manager: CampaignConnectionManager) -> None:
    campaign_id = str(uuid.uuid4())
    user_a = uuid.uuid4()
    user_b = uuid.uuid4()
    socket_a = _socket("a")
    socket_b = _socket("b")

    await manager.connect(campaign_id, socket_a, user_a)
    await manager.connect(campaign_id, socket_b, user_b)
    manager.disconnect(campaign_id, socket_a)

    online = set(manager.get_online_user_ids(campaign_id))
    assert online == {str(user_b)}


@pytest.mark.asyncio
async def test_broadcast_presence_sends_update_to_room(manager: CampaignConnectionManager) -> None:
    campaign_id = str(uuid.uuid4())
    user_id = uuid.uuid4()
    socket = _socket("socket")

    await manager.connect(campaign_id, socket, user_id)
    await manager.broadcast_presence(campaign_id)

    socket.send_json.assert_awaited_once_with(
        {
            "event": "presence_update",
            "online_user_ids": [str(user_id)],
        },
    )


@pytest.mark.asyncio
async def test_send_presence_snapshot_targets_single_socket(manager: CampaignConnectionManager) -> None:
    campaign_id = str(uuid.uuid4())
    user_id = uuid.uuid4()
    socket_a = _socket("a")
    socket_b = _socket("b")

    await manager.connect(campaign_id, socket_a, user_id)
    await manager.connect(campaign_id, socket_b, uuid.uuid4())
    await manager.send_presence_snapshot(campaign_id, socket_a)

    socket_a.send_json.assert_awaited_once_with(
        {
            "event": "presence_snapshot",
            "online_user_ids": manager.get_online_user_ids(campaign_id),
        },
    )
    socket_b.send_json.assert_not_awaited()


@pytest.mark.asyncio
async def test_broadcast_presence_drops_stale_socket(manager: CampaignConnectionManager) -> None:
    campaign_id = str(uuid.uuid4())
    user_id = uuid.uuid4()
    socket = _socket("socket")
    socket.send_json.side_effect = RuntimeError("connection closed")

    await manager.connect(campaign_id, socket, user_id)
    await manager.broadcast_presence(campaign_id)

    assert manager.get_online_user_ids(campaign_id) == []
