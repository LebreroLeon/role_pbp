import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import CampaignOocMessage
from app.models.user import CampaignMember, User
from app.schemas.ooc import OocMessageResponse
from app.services.campaigns import get_user_campaign_role

OOC_PUBLIC = "OOC_PUBLIC"
OOC_WHISPER = "OOC_WHISPER"
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


async def list_ooc_messages(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    viewer_user_id: uuid.UUID,
) -> list[OocMessageResponse]:
    role = await get_user_campaign_role(db, viewer_user_id, campaign_id)
    if role is None:
        raise OocServiceError("Campaign not found")

    author = User.__table__.alias("author")
    target = User.__table__.alias("target")

    rows = await db.execute(
        select(CampaignOocMessage, author.c.display_name, target.c.display_name)
        .join(author, author.c.id == CampaignOocMessage.author_user_id)
        .outerjoin(target, target.c.id == CampaignOocMessage.target_user_id)
        .where(
            CampaignOocMessage.campaign_id == campaign_id,
            or_(
                CampaignOocMessage.message_type == OOC_PUBLIC,
                CampaignOocMessage.author_user_id == viewer_user_id,
                CampaignOocMessage.target_user_id == viewer_user_id,
            ),
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
