import logging
from typing import Any

from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Scene
from app.schemas.scene import SceneResponse

logger = logging.getLogger(__name__)


class SceneConnectionManager:
    def __init__(self) -> None:
        self._rooms: dict[str, set[WebSocket]] = {}

    async def connect(self, scene_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._rooms.setdefault(scene_id, set()).add(websocket)

    def disconnect(self, scene_id: str, websocket: WebSocket) -> None:
        room = self._rooms.get(scene_id)
        if room is None:
            return
        room.discard(websocket)
        if not room:
            self._rooms.pop(scene_id, None)

    async def broadcast(self, scene_id: str, payload: dict[str, Any]) -> None:
        room = list(self._rooms.get(scene_id, set()))
        for websocket in room:
            try:
                await websocket.send_json(payload)
            except Exception:
                logger.debug("Dropping stale websocket for scene %s", scene_id)
                self.disconnect(scene_id, websocket)


scene_ws_manager = SceneConnectionManager()


async def scene_response_with_likes(db: AsyncSession, scene: Scene) -> SceneResponse:
    from app.services.scenes import scene_to_response_with_likes

    return await scene_to_response_with_likes(db, scene)


async def broadcast_scene_update(db: AsyncSession, scene: Scene) -> SceneResponse:
    response = await scene_response_with_likes(db, scene)
    await scene_ws_manager.broadcast(
        str(scene.id),
        {"event": "scene_update", "scene": response.model_dump(mode="json")},
    )
    return response
