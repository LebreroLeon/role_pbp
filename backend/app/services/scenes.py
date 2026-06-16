import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign, Scene
from app.schemas.scene import (
    ChatMessage,
    DiceRollRequest,
    PostMessageRequest,
    SceneCreate,
    SceneResponse,
    SceneState,
)
from app.services.dice import roll_dice as roll_dice_expression
from app.services.master import utc_now_iso
from app.services.rag import rag_service

ALLOWED_MESSAGE_TYPES = {"SPEAK", "ACTION", "CONTEXT", "MASTER", "NARRATIVE", "DICE_ROLL"}


class SceneServiceError(ValueError):
    pass


def normalize_message_type(message_type: str) -> str:
    normalized = message_type.upper()
    if normalized == "NARRATIVE":
        return "ACTION"
    if normalized not in ALLOWED_MESSAGE_TYPES:
        raise SceneServiceError(f"Invalid message type: {message_type}")
    return normalized


def normalize_chat_buffer(buffer: list) -> list[dict]:
    normalized: list[dict] = []
    for index, item in enumerate(buffer):
        data = item if isinstance(item, dict) else item.model_dump()
        entry = dict(data)
        if not entry.get("id"):
            entry["id"] = f"legacy-{index}-{entry.get('timestamp', '')}"
        entry["read_by"] = list(entry.get("read_by") or [])
        if entry.get("type") == "NARRATIVE":
            entry["type"] = "ACTION"
        normalized.append(entry)
    return normalized


def scene_to_response(scene: Scene) -> SceneResponse:
    state_data = dict(scene.scene_state)
    state_data["chat_buffer"] = normalize_chat_buffer(state_data.get("chat_buffer", []))
    state = SceneState.model_validate(state_data)
    return SceneResponse(
        id=str(scene.id),
        campaign_id=str(scene.campaign_id),
        status=scene.status,
        scene_state=state,
    )


async def list_campaign_scenes(db: AsyncSession, campaign_id: uuid.UUID) -> list[SceneResponse]:
    scenes = (
        await db.scalars(
            select(Scene)
            .where(Scene.campaign_id == campaign_id)
            .order_by(Scene.updated_at.desc())
        )
    ).all()
    return [scene_to_response(scene) for scene in scenes]


async def get_active_scene(db: AsyncSession, campaign_id: uuid.UUID) -> Scene | None:
    return await db.scalar(
        select(Scene)
        .where(Scene.campaign_id == campaign_id, Scene.status == "ACTIVE")
        .order_by(Scene.updated_at.desc())
        .limit(1)
    )


async def get_scene_by_id(db: AsyncSession, scene_id: uuid.UUID) -> Scene | None:
    return await db.scalar(select(Scene).where(Scene.id == scene_id))


async def create_scene(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    payload: SceneCreate,
    creator_user_id: uuid.UUID,
) -> SceneResponse:
    campaign = await db.scalar(select(Campaign).where(Campaign.id == campaign_id))
    if campaign is None:
        raise SceneServiceError("Campaign not found")

    existing = await get_active_scene(db, campaign_id)
    if existing is not None:
        raise SceneServiceError("An active scene already exists for this campaign")

    turn_order = payload.turn_order or [str(creator_user_id)]
    scene_state = SceneState(
        campaign_id=str(campaign_id),
        scene_objective=payload.scene_objective,
        turn_order=turn_order,
        current_turn_player_id=turn_order[0] if turn_order else None,
    )

    scene = Scene(
        campaign_id=campaign_id,
        status="ACTIVE",
        scene_state=scene_state.model_dump(),
    )
    db.add(scene)
    await db.commit()
    await db.refresh(scene)
    return scene_to_response(scene)


async def post_message(
    db: AsyncSession,
    scene: Scene,
    sender_id: str,
    payload: PostMessageRequest,
    *,
    sender_role: str = "PLAYER",
) -> SceneResponse:
    msg_type = normalize_message_type(payload.type)
    if msg_type == "MASTER" and sender_role != "MASTER":
        raise SceneServiceError("Master messages require MASTER role")

    state_data = dict(scene.scene_state)
    state_data["chat_buffer"] = normalize_chat_buffer(state_data.get("chat_buffer", []))
    state = SceneState.model_validate(state_data)

    message = {
        "id": str(uuid.uuid4()),
        "timestamp": utc_now_iso(),
        "sender_id": sender_id,
        "type": msg_type,
        "text": payload.text,
        "read_by": [sender_id],
    }
    state.chat_buffer.append(ChatMessage.model_validate(message))
    trimmed = state.chat_buffer[-state.memory_settings.max_chat_buffer_size :]
    state.chat_buffer = trimmed

    scene.scene_state = state.model_dump()
    await db.commit()
    await db.refresh(scene)

    rag_service.index_text(
        campaign_id=state.campaign_id,
        document_id=message["id"],
        text=payload.text,
        metadata={"scene_id": str(scene.id), "sender_id": sender_id, "type": msg_type},
    )
    return scene_to_response(scene)


async def roll_scene_dice(
    db: AsyncSession,
    scene: Scene,
    sender_id: str,
    payload: DiceRollRequest,
) -> SceneResponse:
    state_data = dict(scene.scene_state)
    state_data["chat_buffer"] = normalize_chat_buffer(state_data.get("chat_buffer", []))
    state = SceneState.model_validate(state_data)

    try:
        result = roll_dice_expression(payload.dice_expression, payload.modifier)
    except ValueError as exc:
        raise SceneServiceError(str(exc)) from exc

    message = {
        "id": str(uuid.uuid4()),
        "timestamp": utc_now_iso(),
        "sender_id": sender_id,
        "type": "DICE_ROLL",
        "text": f"Roll: {payload.dice_expression} => {result['final_result']}",
        "dice_expression": payload.dice_expression,
        "raw_result": result["raw_result"],
        "final_result": result["final_result"],
        "skill_checked": payload.skill_checked,
        "read_by": [sender_id],
    }
    state.chat_buffer.append(ChatMessage.model_validate(message))
    state.chat_buffer = state.chat_buffer[-state.memory_settings.max_chat_buffer_size :]

    scene.scene_state = state.model_dump()
    await db.commit()
    await db.refresh(scene)
    return scene_to_response(scene)


async def mark_messages_read(
    db: AsyncSession,
    scene: Scene,
    user_id: str,
    message_ids: list[str] | None = None,
) -> SceneResponse:
    state_data = dict(scene.scene_state)
    buffer = normalize_chat_buffer(state_data.get("chat_buffer", []))

    for entry in buffer:
        if message_ids is not None and entry["id"] not in message_ids:
            continue
        if user_id not in entry["read_by"]:
            entry["read_by"].append(user_id)

    state_data["chat_buffer"] = buffer
    scene.scene_state = state_data
    await db.commit()
    await db.refresh(scene)
    return scene_to_response(scene)


async def update_scene_status(
    db: AsyncSession,
    scene: Scene,
    status: str,
) -> SceneResponse:
    scene.status = status
    state_data = dict(scene.scene_state)
    state_data["status"] = status
    scene.scene_state = state_data
    await db.commit()
    await db.refresh(scene)
    return scene_to_response(scene)
