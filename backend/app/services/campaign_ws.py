import logging
import uuid
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


def user_can_see_ooc_message(
    message_type: str,
    author_user_id: str,
    target_user_id: str | None,
    viewer_user_id: str,
) -> bool:
    if message_type == "OOC_PUBLIC":
        return True
    if message_type != "OOC_WHISPER":
        return False
    return viewer_user_id in {author_user_id, target_user_id}


class CampaignConnectionManager:
    def __init__(self) -> None:
        self._rooms: dict[str, dict[WebSocket, uuid.UUID]] = {}

    def get_online_user_ids(self, campaign_id: str) -> list[str]:
        room = self._rooms.get(campaign_id, {})
        seen: set[str] = set()
        online: list[str] = []
        for user_id in room.values():
            user_id_str = str(user_id)
            if user_id_str in seen:
                continue
            seen.add(user_id_str)
            online.append(user_id_str)
        return online

    async def connect(self, campaign_id: str, websocket: WebSocket, user_id: uuid.UUID) -> None:
        await websocket.accept()
        self._rooms.setdefault(campaign_id, {})[websocket] = user_id

    def disconnect(self, campaign_id: str, websocket: WebSocket) -> None:
        room = self._rooms.get(campaign_id)
        if room is None:
            return
        room.pop(websocket, None)
        if not room:
            self._rooms.pop(campaign_id, None)

    async def send_presence_snapshot(self, campaign_id: str, websocket: WebSocket) -> None:
        await websocket.send_json(
            {
                "event": "presence_snapshot",
                "online_user_ids": self.get_online_user_ids(campaign_id),
            },
        )

    async def broadcast_presence(self, campaign_id: str) -> None:
        payload = {
            "event": "presence_update",
            "online_user_ids": self.get_online_user_ids(campaign_id),
        }
        room = list(self._rooms.get(campaign_id, {}).items())
        for websocket, _user_id in room:
            try:
                await websocket.send_json(payload)
            except Exception:
                logger.debug("Dropping stale websocket for campaign %s", campaign_id)
                self.disconnect(campaign_id, websocket)

    async def broadcast_ooc_message(self, campaign_id: str, message: dict[str, Any]) -> None:
        message_type = str(message.get("message_type", ""))
        author_user_id = str(message.get("author_user_id", ""))
        target_user_id = message.get("target_user_id")
        target_user_id_str = str(target_user_id) if target_user_id else None

        room = list(self._rooms.get(campaign_id, {}).items())
        for websocket, user_id in room:
            if not user_can_see_ooc_message(
                message_type,
                author_user_id,
                target_user_id_str,
                str(user_id),
            ):
                continue
            try:
                await websocket.send_json({"event": "ooc_message", "message": message})
            except Exception:
                logger.debug("Dropping stale websocket for campaign %s", campaign_id)
                self.disconnect(campaign_id, websocket)


campaign_ws_manager = CampaignConnectionManager()
