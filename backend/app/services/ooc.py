import uuid

from sqlalchemy import and_, or_, select, true
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import CampaignOocMessage
from app.models.user import CampaignMember, User
from app.schemas.ooc import OocMessageResponse
from app.services.campaigns import get_user_campaign_role

OOC_PUBLIC = "OOC_PUBLIC"
OOC_WHISPER = "OOC_WHISPER"
OOC_CHANNEL_ALL = "all"
OOC_CHANNEL_MASTER = "master"
MAX_OOC_MESSAGES = 500


class OocServiceError(ValueError):
    pass


def _message_to_response(
    message: CampaignOocMessage,
    author_name: str,
    target_name: str | None,
) -> OocMessageResponse:
    return OocMessageResponse(
        id=str(message.id),
        campaign_id=str(message.campaign_id),
        author_user_id=str(message.author_user_id),
        author_display_name=author_name,
        content=message.content,
        message_type=message.message_type,
        target_user_id=str(message.target_user_id) if message.target_user_id else None,
        target_display_name=target_name,
        created_at=message.created_at,
    )


async def _get_user_display_name(db: AsyncSession, user_id: uuid.UUID) -> str:
    name = await db.scalar(select(User.display_name).where(User.id == user_id))
    return name or "Unknown"


def normalize_ooc_channel(channel: str | None) -> str | None:
    if channel is None:
        return None
    normalized = channel.strip().lower()
    if normalized == "":
        return None
    return normalized


def message_matches_ooc_channel(
    *,
    message_type: str,
    author_user_id: str,
    target_user_id: str | None,
    channel: str,
    viewer_user_id: str,
    master_user_ids: set[str],
    player_user_id: str | None = None,
) -> bool:
    if channel == OOC_CHANNEL_ALL:
        return message_type == OOC_PUBLIC

    if message_type != OOC_WHISPER or target_user_id is None:
        return False

    participants = {author_user_id, target_user_id}

    if channel == OOC_CHANNEL_MASTER:
        return viewer_user_id in participants and bool(participants & master_user_ids)

    if player_user_id is None:
        return False
    return participants == {viewer_user_id, player_user_id}


async def _get_campaign_master_user_ids(
    db: AsyncSession,
    campaign_id: uuid.UUID,
) -> list[uuid.UUID]:
    rows = await db.scalars(
        select(CampaignMember.user_id).where(
            CampaignMember.campaign_id == campaign_id,
            CampaignMember.role == "MASTER",
        )
    )
    return list(rows.all())


async def resolve_ooc_channel(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    viewer_user_id: uuid.UUID,
    viewer_role: str,
    channel: str | None,
) -> str | None:
    normalized = normalize_ooc_channel(channel)
    if normalized is None:
        return None
    if normalized == OOC_CHANNEL_ALL:
        return OOC_CHANNEL_ALL

    if normalized == OOC_CHANNEL_MASTER:
        if viewer_role != "PLAYER":
            raise OocServiceError("Invalid channel")
        return OOC_CHANNEL_MASTER

    try:
        player_id = uuid.UUID(normalized)
    except ValueError as exc:
        raise OocServiceError("Invalid channel") from exc

    if viewer_role != "MASTER":
        raise OocServiceError("Invalid channel")

    target_role = await get_user_campaign_role(db, player_id, campaign_id)
    if target_role != "PLAYER":
        raise OocServiceError("Invalid channel")

    return str(player_id)


def _channel_filter_clause(
    channel: str,
    viewer_user_id: uuid.UUID,
    master_user_ids: list[uuid.UUID],
):
    if channel == OOC_CHANNEL_ALL:
        return CampaignOocMessage.message_type == OOC_PUBLIC

    if channel == OOC_CHANNEL_MASTER:
        master_ids = master_user_ids or [uuid.UUID(int=0)]
        return and_(
            CampaignOocMessage.message_type == OOC_WHISPER,
            or_(
                and_(
                    CampaignOocMessage.author_user_id == viewer_user_id,
                    CampaignOocMessage.target_user_id.in_(master_ids),
                ),
                and_(
                    CampaignOocMessage.target_user_id == viewer_user_id,
                    CampaignOocMessage.author_user_id.in_(master_ids),
                ),
            ),
        )

    player_id = uuid.UUID(channel)
    return and_(
        CampaignOocMessage.message_type == OOC_WHISPER,
        or_(
            and_(
                CampaignOocMessage.author_user_id == viewer_user_id,
                CampaignOocMessage.target_user_id == player_id,
            ),
            and_(
                CampaignOocMessage.target_user_id == viewer_user_id,
                CampaignOocMessage.author_user_id == player_id,
            ),
        ),
    )


async def list_ooc_messages(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    viewer_user_id: uuid.UUID,
    *,
    channel: str | None = None,
) -> list[OocMessageResponse]:
    role = await get_user_campaign_role(db, viewer_user_id, campaign_id)
    if role is None:
        raise OocServiceError("Campaign not found")

    resolved_channel = await resolve_ooc_channel(db, campaign_id, viewer_user_id, role, channel)
    master_user_ids = await _get_campaign_master_user_ids(db, campaign_id)

    author = User.__table__.alias("author")
    target = User.__table__.alias("target")

    if resolved_channel is None:
        visibility = or_(
            CampaignOocMessage.message_type == OOC_PUBLIC,
            CampaignOocMessage.author_user_id == viewer_user_id,
            CampaignOocMessage.target_user_id == viewer_user_id,
        )
        channel_clause = true()
    elif resolved_channel == OOC_CHANNEL_ALL:
        visibility = CampaignOocMessage.message_type == OOC_PUBLIC
        channel_clause = true()
    else:
        visibility = or_(
            CampaignOocMessage.message_type == OOC_PUBLIC,
            CampaignOocMessage.author_user_id == viewer_user_id,
            CampaignOocMessage.target_user_id == viewer_user_id,
        )
        channel_clause = _channel_filter_clause(resolved_channel, viewer_user_id, master_user_ids)

    rows = await db.execute(
        select(CampaignOocMessage, author.c.display_name, target.c.display_name)
        .join(author, author.c.id == CampaignOocMessage.author_user_id)
        .outerjoin(target, target.c.id == CampaignOocMessage.target_user_id)
        .where(
            CampaignOocMessage.campaign_id == campaign_id,
            visibility,
            channel_clause,
        )
        .order_by(CampaignOocMessage.created_at.asc())
        .limit(MAX_OOC_MESSAGES)
    )

    return [
        _message_to_response(message, author_name, target_name)
        for message, author_name, target_name in rows.all()
    ]


async def _ensure_campaign_member(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    role = await get_user_campaign_role(db, user_id, campaign_id)
    if role is None:
        raise OocServiceError("Campaign not found")


async def _ensure_target_member(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    target_user_id: uuid.UUID,
) -> None:
    member = await db.scalar(
        select(CampaignMember).where(
            CampaignMember.campaign_id == campaign_id,
            CampaignMember.user_id == target_user_id,
        )
    )
    if member is None:
        raise OocServiceError("Target user is not a campaign member")


async def post_ooc_public(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    author_user_id: uuid.UUID,
    content: str,
) -> OocMessageResponse:
    await _ensure_campaign_member(db, campaign_id, author_user_id)

    text = content.strip()
    if not text:
        raise OocServiceError("Empty message")

    message = CampaignOocMessage(
        campaign_id=campaign_id,
        author_user_id=author_user_id,
        content=text,
        message_type=OOC_PUBLIC,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)

    author_name = await _get_user_display_name(db, author_user_id)
    return _message_to_response(message, author_name, None)


async def post_ooc_whisper(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    author_user_id: uuid.UUID,
    target_user_id: uuid.UUID,
    content: str,
) -> OocMessageResponse:
    await _ensure_campaign_member(db, campaign_id, author_user_id)
    await _ensure_target_member(db, campaign_id, target_user_id)

    author_role = await get_user_campaign_role(db, author_user_id, campaign_id)
    target_role = await get_user_campaign_role(db, target_user_id, campaign_id)
    if author_role == "PLAYER" and target_role != "MASTER":
        raise OocServiceError("Players can only message the master privately")
    if author_role == "MASTER" and target_role != "PLAYER":
        raise OocServiceError("Master can only message players privately")

    if target_user_id == author_user_id:
        raise OocServiceError("Cannot whisper to yourself")

    text = content.strip()
    if not text:
        raise OocServiceError("Empty message")

    message = CampaignOocMessage(
        campaign_id=campaign_id,
        author_user_id=author_user_id,
        content=text,
        message_type=OOC_WHISPER,
        target_user_id=target_user_id,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)

    author_name = await _get_user_display_name(db, author_user_id)
    target_name = await _get_user_display_name(db, target_user_id)
    return _message_to_response(message, author_name, target_name)
