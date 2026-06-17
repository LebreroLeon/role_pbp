import uuid

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_user_from_token, require_campaign_member
from app.core.database import SessionLocal
from app.schemas.scene import DiceRollRequest, PostMessageRequest
from app.services.scene_ws import scene_ws_manager
from app.services.scenes import (
    SceneServiceError,
    get_scene_by_id,
    mark_messages_read,
    post_message,
    roll_scene_dice,
    scene_to_response,
)

router = APIRouter(tags=["websocket"])


async def _authenticate_ws(token: str, db: AsyncSession):
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
            role = await require_campaign_member(db, user, scene.campaign_id)
            snapshot = scene_to_response(scene)
            member_role = role
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
                role = await require_campaign_member(db, user, scene.campaign_id)

                try:
                    if action == "message":
                        text = str(data.get("text", "")).strip()
                        if not text:
                            await websocket.send_json({"event": "error", "detail": "Empty message"})
                            continue
                        msg_type = str(data.get("message_type", "ACTION")).upper()
                        speaker_entity_id = data.get("speaker_entity_id")
                        speaker_display_name = data.get("speaker_display_name")
                        speaker_type = data.get("speaker_type")
                        response = await post_message(
                            db,
                            scene,
                            str(user.id),
                            PostMessageRequest(
                                type=msg_type,
                                text=text,
                                speaker_entity_id=(
                                    str(speaker_entity_id) if speaker_entity_id else None
                                ),
                                speaker_display_name=(
                                    str(speaker_display_name) if speaker_display_name else None
                                ),
                                speaker_type=speaker_type,
                            ),
                            sender_role=role,
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
                    elif action == "mark_read":
                        message_ids = data.get("message_ids")
                        ids = (
                            message_ids
                            if isinstance(message_ids, list) and len(message_ids) > 0
                            else None
                        )
                        response = await mark_messages_read(db, scene, str(user.id), ids)
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
