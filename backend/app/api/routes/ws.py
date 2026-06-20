import uuid

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import PLAYER_NO_ACTIVE_SCENE_DETAIL, get_user_from_token, require_campaign_member
from app.core.database import SessionLocal
from app.schemas.scene import DiceRollRequest, PostMessageRequest
from app.services.campaign_ws import campaign_ws_manager
from app.services.ooc import OocServiceError, list_ooc_messages, post_ooc_public, post_ooc_whisper
from app.services.scene_ws import broadcast_scene_update, scene_response_with_likes
from app.services.scenes import (
    SceneServiceError,
    get_scene_by_id,
    mark_messages_read,
    post_message,
    roll_scene_dice,
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
            if role != "MASTER" and scene.status == "CLOSED":
                await websocket.close(code=4403, reason=PLAYER_NO_ACTIVE_SCENE_DETAIL)
                return
            snapshot = await scene_response_with_likes(db, scene)
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
                if role != "MASTER" and scene.status == "CLOSED":
                    await websocket.send_json(
                        {"event": "error", "detail": PLAYER_NO_ACTIVE_SCENE_DETAIL},
                    )
                    continue

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
                        await post_message(
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
                        await roll_scene_dice(
                            db,
                            scene,
                            str(user.id),
                            DiceRollRequest(
                                dice_expression=expression,
                                modifier=int(data.get("modifier") or 0),
                                advantage=bool(data.get("advantage")),
                                disadvantage=bool(data.get("disadvantage")),
                            ),
                            sender_role=role,
                        )
                    elif action == "mark_read":
                        message_ids = data.get("message_ids")
                        ids = (
                            message_ids
                            if isinstance(message_ids, list) and len(message_ids) > 0
                            else None
                        )
                        await mark_messages_read(db, scene, str(user.id), ids)
                    else:
                        await websocket.send_json({"event": "error", "detail": "Unknown action"})
                        continue
                except SceneServiceError as exc:
                    await websocket.send_json({"event": "error", "detail": str(exc)})
                    continue

            await broadcast_scene_update(db, scene)
    except WebSocketDisconnect:
        pass
    finally:
        scene_ws_manager.disconnect(scene_id, websocket)


@router.websocket("/ws/campaigns/{campaign_id}")
async def campaign_websocket(campaign_id: str, websocket: WebSocket, token: str = "") -> None:
    try:
        campaign_uuid = uuid.UUID(campaign_id)
    except ValueError:
        await websocket.close(code=4400)
        return

    async with SessionLocal() as db:
        try:
            user = await _authenticate_ws(token, db)
            await require_campaign_member(db, user, campaign_uuid)
            initial_messages = await list_ooc_messages(db, campaign_uuid, user.id)
        except HTTPException:
            await websocket.close(code=4401)
            return
        except OocServiceError:
            await websocket.close(code=4404)
            return

    await campaign_ws_manager.connect(campaign_id, websocket, user.id)

    try:
        await websocket.send_json(
            {
                "event": "ooc_snapshot",
                "messages": [message.model_dump(mode="json") for message in initial_messages],
            },
        )
        await campaign_ws_manager.send_presence_snapshot(campaign_id, websocket)
        await campaign_ws_manager.broadcast_presence(campaign_id)

        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            async with SessionLocal() as db:
                user = await _authenticate_ws(token, db)
                await require_campaign_member(db, user, campaign_uuid)

                try:
                    if action == "ooc_public":
                        text = str(data.get("content", "")).strip()
                        if not text:
                            await websocket.send_json({"event": "error", "detail": "Empty message"})
                            continue
                        message = await post_ooc_public(db, campaign_uuid, user.id, text)
                    elif action == "ooc_whisper":
                        text = str(data.get("content", "")).strip()
                        target_user_id = data.get("target_user_id")
                        if not text:
                            await websocket.send_json({"event": "error", "detail": "Empty message"})
                            continue
                        if not target_user_id:
                            await websocket.send_json({"event": "error", "detail": "Missing target_user_id"})
                            continue
                        try:
                            target_uuid = uuid.UUID(str(target_user_id))
                        except ValueError:
                            await websocket.send_json({"event": "error", "detail": "Invalid target_user_id"})
                            continue
                        message = await post_ooc_whisper(db, campaign_uuid, user.id, target_uuid, text)
                    elif action == "heartbeat":
                        await websocket.send_json({"event": "heartbeat_ack"})
                        continue
                    else:
                        await websocket.send_json({"event": "error", "detail": "Unknown action"})
                        continue
                except OocServiceError as exc:
                    await websocket.send_json({"event": "error", "detail": str(exc)})
                    continue

            await campaign_ws_manager.broadcast_ooc_message(
                campaign_id,
                message.model_dump(mode="json"),
            )
    except WebSocketDisconnect:
        pass
    finally:
        campaign_ws_manager.disconnect(campaign_id, websocket)
        await campaign_ws_manager.broadcast_presence(campaign_id)
