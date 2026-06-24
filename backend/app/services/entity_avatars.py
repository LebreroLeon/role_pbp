import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.campaign import CampaignEntity
from app.schemas.entities import EntityType
from app.services.object_storage import (
    ALLOWED_EXTENSIONS,
    avatar_storage_key,
    find_existing_image_key,
    get_storage_backend,
    media_type_for_extension,
)

MIME_SUFFIX_MAP = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


class EntityAvatarError(ValueError):
    pass


def avatar_api_path(entity_id: uuid.UUID) -> str:
    return f"/api/v1/entities/{entity_id}/avatar"


def _safe_image_extension(filename: str, mime_type: str | None) -> str:
    from pathlib import Path

    suffix = Path(filename).suffix.lower()
    if suffix == ".jpeg":
        suffix = ".jpg"
    if suffix in ALLOWED_EXTENSIONS:
        return suffix if suffix != ".jpeg" else ".jpg"
    if mime_type:
        mapped = MIME_SUFFIX_MAP.get(mime_type.lower())
        if mapped:
            return mapped
    raise EntityAvatarError(
        f"Tipo de imagen no permitido. Permitidos: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
    )


def resolve_entity_avatar_storage(entity: CampaignEntity) -> tuple[str, str] | None:
    """Return (storage_key, media_type) when the entity has a stored avatar."""
    avatar_url = read_entity_avatar_url(entity)
    if not avatar_url or not avatar_url.endswith("/avatar"):
        return None

    storage = get_storage_backend()
    return find_existing_image_key(
        storage,
        campaign_id=entity.campaign_id,
        entity_id=entity.id,
        category="avatars",
        allowed_extensions=ALLOWED_EXTENSIONS,
    )


def read_entity_avatar_url(entity: CampaignEntity) -> str | None:
    document = entity.document
    if entity.entity_type == EntityType.PC.value:
        profile = document.get("public_profile")
    elif entity.entity_type == EntityType.NPC.value:
        profile = document.get("ai_narrative_profile")
    else:
        return None
    if not isinstance(profile, dict):
        return None
    raw = profile.get("avatar_url")
    return raw.strip() if isinstance(raw, str) and raw.strip() else None


def write_entity_avatar_url(entity: CampaignEntity, url: str | None) -> None:
    document = dict(entity.document)
    if entity.entity_type == EntityType.PC.value:
        profile_key = "public_profile"
    elif entity.entity_type == EntityType.NPC.value:
        profile_key = "ai_narrative_profile"
    else:
        raise EntityAvatarError("Solo PC y NPC admiten avatar")

    profile = document.get(profile_key)
    if not isinstance(profile, dict):
        raise EntityAvatarError("Documento de entidad incompleto")

    profile = dict(profile)
    if url:
        profile["avatar_url"] = url
    else:
        profile.pop("avatar_url", None)
    document[profile_key] = profile
    entity.document = document


def _delete_existing_avatar_objects(entity: CampaignEntity) -> None:
    storage = get_storage_backend()
    for suffix in ALLOWED_EXTENSIONS:
        normalized = ".jpg" if suffix == ".jpeg" else suffix
        key = avatar_storage_key(entity.campaign_id, entity.id, normalized)
        if storage.exists(key):
            storage.delete_object(key)


async def save_entity_avatar_file(
    db: AsyncSession,
    entity: CampaignEntity,
    *,
    original_name: str,
    content: bytes,
    mime_type: str | None,
) -> str:
    if entity.entity_type not in (EntityType.PC.value, EntityType.NPC.value):
        raise EntityAvatarError("Solo PC y NPC admiten avatar")
    if len(content) > settings.max_upload_bytes:
        raise EntityAvatarError(
            f"Imagen demasiado grande (máx. {settings.max_upload_bytes // (1024 * 1024)} MB)"
        )

    suffix = _safe_image_extension(original_name, mime_type)
    storage = get_storage_backend()
    _delete_existing_avatar_objects(entity)

    key = avatar_storage_key(entity.campaign_id, entity.id, suffix)
    content_type = mime_type or media_type_for_extension(suffix)
    storage.put_object(key, content, content_type=content_type)

    url = avatar_api_path(entity.id)
    write_entity_avatar_url(entity, url)
    await db.commit()
    await db.refresh(entity)
    return url


async def clear_entity_avatar_file(db: AsyncSession, entity: CampaignEntity) -> None:
    _delete_existing_avatar_objects(entity)
    write_entity_avatar_url(entity, None)
    await db.commit()
    await db.refresh(entity)
