import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import SceneMessageLike


async def fetch_likes_by_message_id(
    db: AsyncSession,
    scene_id: uuid.UUID,
    message_ids: list[str],
) -> dict[str, list[str]]:
    if not message_ids:
        return {}

    rows = (
        await db.scalars(
            select(SceneMessageLike).where(
                SceneMessageLike.scene_id == scene_id,
                SceneMessageLike.message_id.in_(message_ids),
            )
        )
    ).all()

    likes: dict[str, list[str]] = {}
    for row in rows:
        likes.setdefault(row.message_id, []).append(str(row.user_id))
    return likes


async def toggle_message_like(
    db: AsyncSession,
    scene_id: uuid.UUID,
    message_id: str,
    user_id: uuid.UUID,
) -> bool:
    """Toggle like. Returns True if liked after toggle, False if unliked."""
    existing = await db.scalar(
        select(SceneMessageLike).where(
            SceneMessageLike.scene_id == scene_id,
            SceneMessageLike.message_id == message_id,
            SceneMessageLike.user_id == user_id,
        )
    )

    if existing:
        await db.delete(existing)
        return False

    db.add(
        SceneMessageLike(
            scene_id=scene_id,
            message_id=message_id,
            user_id=user_id,
        )
    )
    return True


async def delete_likes_for_message(
    db: AsyncSession,
    scene_id: uuid.UUID,
    message_id: str,
) -> None:
    await db.execute(
        delete(SceneMessageLike).where(
            SceneMessageLike.scene_id == scene_id,
            SceneMessageLike.message_id == message_id,
        )
    )
