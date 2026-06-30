import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import SceneMessage
from app.schemas.scene import ChatMessage
from app.services.message_likes import fetch_likes_by_message_id

DEFAULT_SCENE_MESSAGE_PAGE_SIZE = 50
MAX_SCENE_MESSAGE_PAGE_SIZE = 100


def _parse_message_timestamp(timestamp: str | None) -> datetime:
    if not timestamp:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)


def payload_from_chat_message(message: ChatMessage | dict) -> dict:
    data = message if isinstance(message, dict) else message.model_dump()
    return {
        key: value
        for key, value in data.items()
        if key not in ("like_count", "liked_by_user_ids")
    }


def chat_message_from_row(row: SceneMessage) -> ChatMessage:
    return ChatMessage.model_validate(row.payload)


def filter_chat_message_for_viewer(message: ChatMessage, viewer_role: str) -> ChatMessage | None:
    if viewer_role == "MASTER":
        return message
    if (message.visibility or "all") == "master_only":
        return None
    return message


def apply_likes_to_chat_messages(
    messages: list[ChatMessage],
    likes_by_message_id: dict[str, list[str]],
) -> None:
    for message in messages:
        if not message.id:
            message.like_count = 0
            message.liked_by_user_ids = []
            continue
        user_ids = likes_by_message_id.get(message.id, [])
        message.liked_by_user_ids = user_ids
        message.like_count = len(user_ids)


async def persist_scene_message(
    db: AsyncSession,
    scene_id: uuid.UUID,
    message: ChatMessage | dict,
) -> None:
    msg = ChatMessage.model_validate(message)
    if not msg.id:
        raise ValueError("Scene message id is required")

    payload = payload_from_chat_message(msg)
    created_at = _parse_message_timestamp(msg.timestamp)
    existing = await db.get(SceneMessage, msg.id)
    if existing is not None:
        existing.payload = payload
        existing.created_at = created_at
        return

    db.add(
        SceneMessage(
            id=msg.id,
            scene_id=scene_id,
            payload=payload,
            created_at=created_at,
        )
    )


async def delete_persisted_scene_message(
    db: AsyncSession,
    scene_id: uuid.UUID,
    message_id: str,
) -> bool:
    row = await db.get(SceneMessage, message_id)
    if row is None or row.scene_id != scene_id:
        return False
    await db.delete(row)
    return True


async def update_persisted_read_by(
    db: AsyncSession,
    scene_id: uuid.UUID,
    user_id: str,
    message_ids: list[str] | None = None,
) -> None:
    query = select(SceneMessage).where(SceneMessage.scene_id == scene_id)
    if message_ids is not None:
        if not message_ids:
            return
        query = query.where(SceneMessage.id.in_(message_ids))

    rows = (await db.scalars(query)).all()
    for row in rows:
        payload = dict(row.payload)
        read_by = list(payload.get("read_by") or [])
        if user_id not in read_by:
            read_by.append(user_id)
            payload["read_by"] = read_by
            row.payload = payload


async def list_scene_messages(
    db: AsyncSession,
    scene_id: uuid.UUID,
    *,
    before_message_id: str | None = None,
    before_timestamp: str | None = None,
    limit: int = DEFAULT_SCENE_MESSAGE_PAGE_SIZE,
    viewer_role: str = "PLAYER",
) -> list[ChatMessage]:
    page_size = max(1, min(limit, MAX_SCENE_MESSAGE_PAGE_SIZE))
    query = select(SceneMessage).where(SceneMessage.scene_id == scene_id)

    if before_message_id or before_timestamp:
        cutoff: datetime | None = None
        if before_message_id:
            before_row = await db.get(SceneMessage, before_message_id)
            if before_row is not None and before_row.scene_id == scene_id:
                cutoff = before_row.created_at
        if cutoff is None and before_timestamp:
            cutoff = _parse_message_timestamp(before_timestamp)
        if cutoff is not None:
            query = query.where(SceneMessage.created_at < cutoff)

    rows = (
        await db.scalars(
            query.order_by(SceneMessage.created_at.desc()).limit(page_size)
        )
    ).all()
    rows.reverse()

    messages: list[ChatMessage] = []
    for row in rows:
        message = chat_message_from_row(row)
        filtered = filter_chat_message_for_viewer(message, viewer_role)
        if filtered is not None:
            messages.append(filtered)

    message_ids = [message.id for message in messages if message.id]
    likes = await fetch_likes_by_message_id(db, scene_id, message_ids)
    apply_likes_to_chat_messages(messages, likes)
    return messages


async def list_all_scene_messages(
    db: AsyncSession,
    scene_id: uuid.UUID,
) -> list[ChatMessage]:
    rows = (
        await db.scalars(
            select(SceneMessage)
            .where(SceneMessage.scene_id == scene_id)
            .order_by(SceneMessage.created_at.asc())
        )
    ).all()
    return [chat_message_from_row(row) for row in rows]


async def scene_has_older_messages(
    db: AsyncSession,
    scene_id: uuid.UUID,
    *,
    oldest_visible_message_id: str | None,
    oldest_visible_timestamp: str | None = None,
) -> bool:
    if not oldest_visible_message_id and not oldest_visible_timestamp:
        count = await db.scalar(
            select(func.count()).select_from(SceneMessage).where(SceneMessage.scene_id == scene_id)
        )
        return bool(count)

    cutoff: datetime | None = None
    if oldest_visible_message_id:
        oldest_row = await db.get(SceneMessage, oldest_visible_message_id)
        if oldest_row is not None and oldest_row.scene_id == scene_id:
            cutoff = oldest_row.created_at
    if cutoff is None and oldest_visible_timestamp:
        cutoff = _parse_message_timestamp(oldest_visible_timestamp)
    if cutoff is None:
        return False

    older_count = await db.scalar(
        select(func.count())
        .select_from(SceneMessage)
        .where(
            SceneMessage.scene_id == scene_id,
            SceneMessage.created_at < cutoff,
        )
    )
    return bool(older_count)
