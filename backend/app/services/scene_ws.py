import logging
from typing import Any

from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Scene
from app.schemas.scene import SceneResponse
from app.services.campaign_ws import campaign_ws_manager

logger = logging.getLogger(__name__)


class SceneConnectionManager:
    def __init__(self) -> None:
        self._rooms: dict[str, dict[WebSocket, str]] = {}

    async def connect(self, scene_id: str, websocket: WebSocket, *, role: str) -> None:
        await websocket.accept()
        self._rooms.setdefault(scene_id, {})[websocket] = role

    def disconnect(self, scene_id: str, websocket: WebSocket) -> None:
        room = self._rooms.get(scene_id)
        if room is None:
            return
        room.pop(websocket, None)
        if not room:
            self._rooms.pop(scene_id, None)

    def roles_for_scene(self, scene_id: str) -> dict[WebSocket, str]:
        return dict(self._rooms.get(scene_id, {}))

    async def broadcast(self, scene_id: str, build_payload: Any) -> None:
        room = self.roles_for_scene(scene_id)
        for websocket, role in room.items():
            try:
                payload = await build_payload(role)
                await websocket.send_json(payload)
            except Exception:
                logger.debug("Dropping stale websocket for scene %s", scene_id)
                self.disconnect(scene_id, websocket)


scene_ws_manager = SceneConnectionManager()


async def scene_response_with_likes(
    db: AsyncSession,
    scene: Scene,
    *,
    viewer_role: str = "MASTER",
) -> SceneResponse:
    from app.services.scenes import scene_to_response_with_likes

    return await scene_to_response_with_likes(db, scene, viewer_role=viewer_role)


async def broadcast_scene_update(
    db: AsyncSession,
    scene: Scene,
    *,
    requester_role: str = "MASTER",
) -> SceneResponse:
    scene_id = str(scene.id)

    async def build_payload(role: str) -> dict[str, Any]:
        response = await scene_response_with_likes(db, scene, viewer_role=role)
        return {"event": "scene_update", "scene": response.model_dump(mode="json")}

    await scene_ws_manager.broadcast(scene_id, build_payload)
    await campaign_ws_manager.broadcast_unread_counts(db, str(scene.campaign_id))
    return await scene_response_with_likes(db, scene, viewer_role=requester_role)
