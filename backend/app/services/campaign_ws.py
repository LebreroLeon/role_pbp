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
