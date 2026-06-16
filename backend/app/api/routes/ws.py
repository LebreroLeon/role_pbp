import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_user_from_token, require_campaign_member
from app.core.database import SessionLocal
from app.models.user import User
from app.schemas.scene import DiceRollRequest, PostMessageRequest
from app.services.scene_ws import scene_ws_manager
from app.services.scenes import (
    SceneServiceError,
    get_scene_by_id,
    post_message,
    roll_scene_dice,
    scene_to_response,
)

router = APIRouter(tags=["websocket"])


async def _authenticate_ws(token: str, db: AsyncSession) -> User:
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return await get_user_from_token(db, token)


@router.websocket("/ws/scenes/{scene_id}")
async def scene_websocket(scene_id: str, websocket: WebSocket, token: str = "") -> None:
    try:
        scene_uuid = uuid.UUID(scene_id)
    except ValueError:
        await websocket.close(code=4400)
        return

    async with SessionLocal() as db:
        try:
            user = await _authenticate_ws(token, db)
            scene = await get_scene_by_id(db, scene_uuid)
            if scene is None:
                await websocket.close(code=4404)
                return
            await require_campaign_member(db, user, scene.campaign_id)
            snapshot = scene_to_response(scene)
        except HTTPException:
            await websocket.close(code=4401)
            return

    await scene_ws_manager.connect(scene_id, websocket)

    try:
        await websocket.send_json(
            {"event": "scene_snapshot", "scene": snapshot.model_dump(mode="json")},
        )

        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            async with SessionLocal() as db:
                user = await _authenticate_ws(token, db)
                scene = await get_scene_by_id(db, scene_uuid)
                if scene is None:
                    await websocket.send_json({"event": "error", "detail": "Scene not found"})
                    continue
                await require_campaign_member(db, user, scene.campaign_id)

                try:
                    if action == "message":
                        text = str(data.get("text", "")).strip()
                        if not text:
                            await websocket.send_json({"event": "error", "detail": "Empty message"})
                            continue
                        response = await post_message(
                            db,
                            scene,
                            str(user.id),
                            PostMessageRequest(text=text),
                        )
                    elif action == "dice":
                        expression = str(data.get("dice_expression", "")).strip()
                        if not expression:
                            await websocket.send_json({"event": "error", "detail": "Missing dice expression"})
                            continue
                        response = await roll_scene_dice(
                            db,
                            scene,
                            str(user.id),
                            DiceRollRequest(dice_expression=expression),
                        )
                    else:
                        await websocket.send_json({"event": "error", "detail": "Unknown action"})
                        continue
                except SceneServiceError as exc:
                    await websocket.send_json({"event": "error", "detail": str(exc)})
                    continue

            payload = {"event": "scene_update", "scene": response.model_dump(mode="json")}
            await scene_ws_manager.broadcast(scene_id, payload)
    except WebSocketDisconnect:
        pass
    finally:
        scene_ws_manager.disconnect(scene_id, websocket)
