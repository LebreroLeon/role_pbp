import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.campaign import CampaignEntity
from app.schemas.entities import EntityType

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MIME_SUFFIX_MAP = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


class EntityAvatarError(ValueError):
    pass


def _upload_root() -> Path:
    root = Path(settings.upload_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


def avatar_api_path(entity_id: uuid.UUID) -> str:
    return f"/api/v1/entities/{entity_id}/avatar"


def _safe_image_extension(filename: str, mime_type: str | None) -> str:
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


def _avatar_dir(campaign_id: uuid.UUID) -> Path:
    return _upload_root() / str(campaign_id) / "avatars"


def resolve_entity_avatar_path(entity: CampaignEntity) -> Path | None:
    avatar_url = read_entity_avatar_url(entity)
    if not avatar_url or not avatar_url.endswith("/avatar"):
        return None

    directory = _avatar_dir(entity.campaign_id)
    if not directory.exists():
        return None

    for suffix in ALLOWED_EXTENSIONS:
        normalized = ".jpg" if suffix == ".jpeg" else suffix
        path = directory / f"{entity.id}{normalized}"
        if path.exists():
            return path
    return None


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


def _delete_existing_avatar_files(entity: CampaignEntity) -> None:
    directory = _avatar_dir(entity.campaign_id)
    if not directory.exists():
        return
    for suffix in ALLOWED_EXTENSIONS:
        normalized = ".jpg" if suffix == ".jpeg" else suffix
        path = directory / f"{entity.id}{normalized}"
        if path.exists():
            path.unlink()


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
    avatar_dir = _avatar_dir(entity.campaign_id)
    avatar_dir.mkdir(parents=True, exist_ok=True)

    _delete_existing_avatar_files(entity)
    file_path = avatar_dir / f"{entity.id}{suffix}"
    file_path.write_bytes(content)

    url = avatar_api_path(entity.id)
    write_entity_avatar_url(entity, url)
    await db.commit()
    await db.refresh(entity)
    return url


async def clear_entity_avatar_file(db: AsyncSession, entity: CampaignEntity) -> None:
    _delete_existing_avatar_files(entity)
    write_entity_avatar_url(entity, None)
    await db.commit()
    await db.refresh(entity)
