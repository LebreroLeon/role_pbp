import uuid
from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import CampaignOocMessage, CampaignOocReadState, Scene
from app.schemas.unread import UnreadCountsResponse
from app.services.ooc import OOC_PUBLIC, OOC_WHISPER
from app.services.scenes import filter_scene_state_for_viewer, get_open_scene, load_scene_state


def count_play_unread(
    scene: Scene | None,
    user_id: str,
    *,
    viewer_role: str,
) -> int:
    if scene is None or scene.status == "CLOSED":
        return 0

    state = load_scene_state(scene)
    filtered = filter_scene_state_for_viewer(state, viewer_role)
    unread = 0
    for message in filtered.chat_buffer:
        if message.sender_id == user_id:
            continue
        if user_id not in (message.read_by or []):
            unread += 1
    return unread


async def get_ooc_last_read_at(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    user_id: uuid.UUID,
) -> datetime | None:
    return await db.scalar(
        select(CampaignOocReadState.last_read_at).where(
            CampaignOocReadState.campaign_id == campaign_id,
            CampaignOocReadState.user_id == user_id,
        )
    )


async def count_ooc_unread(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    user_id: uuid.UUID,
) -> int:
    last_read_at = await get_ooc_last_read_at(db, campaign_id, user_id)

    query = select(func.count()).select_from(CampaignOocMessage).where(
        CampaignOocMessage.campaign_id == campaign_id,
        CampaignOocMessage.author_user_id != user_id,
        or_(
            CampaignOocMessage.message_type == OOC_PUBLIC,
            CampaignOocMessage.target_user_id == user_id,
        ),
    )
    if last_read_at is not None:
        query = query.where(CampaignOocMessage.created_at > last_read_at)

    return int(await db.scalar(query) or 0)


async def get_unread_counts(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    viewer_role: str,
) -> UnreadCountsResponse:
    scene = await get_open_scene(db, campaign_id)
    play = count_play_unread(scene, str(user_id), viewer_role=viewer_role)
    ooc = await count_ooc_unread(db, campaign_id, user_id)
    return UnreadCountsResponse(play=play, ooc=ooc)


async def mark_ooc_read(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    now = datetime.now(timezone.utc)
    stmt = insert(CampaignOocReadState).values(
        campaign_id=campaign_id,
        user_id=user_id,
        last_read_at=now,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["campaign_id", "user_id"],
        set_={"last_read_at": now},
    )
    await db.execute(stmt)
    await db.commit()
