import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.campaign import CampaignEntity
from app.schemas.entities import EntityType
from app.services.entities import npc_player_visibility

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MIME_SUFFIX_MAP = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

ILLUSTRATION_ENTITY_TYPES = {
    EntityType.NPC.value,
    EntityType.PC.value,
    EntityType.FACTION.value,
    EntityType.LOCATION.value,
    EntityType.RELATIONSHIP.value,
}


class EntityIllustrationError(ValueError):
    pass


def _upload_root() -> Path:
    root = Path(settings.upload_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


def illustration_api_path(entity_id: uuid.UUID) -> str:
    return f"/api/v1/entities/{entity_id}/illustration"


def _profile_key(entity_type: str) -> str:
    if entity_type == EntityType.PC.value:
        return "public_profile"
    if entity_type == EntityType.NPC.value:
        return "ai_narrative_profile"
    if entity_type in (EntityType.FACTION.value, EntityType.LOCATION.value):
        return "narrative_profile"
    if entity_type == EntityType.RELATIONSHIP.value:
        return "narrative_bond"
    raise EntityIllustrationError("Tipo de entidad no admite ilustración")


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
    raise EntityIllustrationError(
        f"Tipo de imagen no permitido. Permitidos: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
    )


def _illustration_dir(campaign_id: uuid.UUID) -> Path:
    return _upload_root() / str(campaign_id) / "illustrations"


def resolve_entity_illustration_path(entity: CampaignEntity) -> Path | None:
    illustration_url = read_entity_illustration_url(entity)
    if not illustration_url or not illustration_url.endswith("/illustration"):
        return None

    directory = _illustration_dir(entity.campaign_id)
    if not directory.exists():
        return None

    for suffix in ALLOWED_EXTENSIONS:
        normalized = ".jpg" if suffix == ".jpeg" else suffix
        path = directory / f"{entity.id}{normalized}"
        if path.exists():
            return path
    return None


def read_entity_illustration_url(entity: CampaignEntity) -> str | None:
    if entity.entity_type not in ILLUSTRATION_ENTITY_TYPES:
        return None

    document = entity.document
    profile_key = _profile_key(entity.entity_type)
    profile = document.get(profile_key)
    if not isinstance(profile, dict):
        return None
    raw = profile.get("illustration_url")
    return raw.strip() if isinstance(raw, str) and raw.strip() else None


def write_entity_illustration_url(entity: CampaignEntity, url: str | None) -> None:
    if entity.entity_type not in ILLUSTRATION_ENTITY_TYPES:
        raise EntityIllustrationError("Tipo de entidad no admite ilustración")

    document = dict(entity.document)
    profile_key = _profile_key(entity.entity_type)
    profile = document.get(profile_key)
    if not isinstance(profile, dict):
        raise EntityIllustrationError("Documento de entidad incompleto")

    profile = dict(profile)
    if url:
        profile["illustration_url"] = url
    else:
        profile.pop("illustration_url", None)
    document[profile_key] = profile
    entity.document = document


def player_can_view_entity_illustration(entity: CampaignEntity) -> bool:
    if entity.entity_type == EntityType.NPC.value:
        return npc_player_visibility(entity.document) == "visible"
    return entity.entity_type in ILLUSTRATION_ENTITY_TYPES


def _delete_existing_illustration_files(entity: CampaignEntity) -> None:
    directory = _illustration_dir(entity.campaign_id)
    if not directory.exists():
        return
    for suffix in ALLOWED_EXTENSIONS:
        normalized = ".jpg" if suffix == ".jpeg" else suffix
        path = directory / f"{entity.id}{normalized}"
        if path.exists():
            path.unlink()


async def save_entity_illustration_file(
    db: AsyncSession,
    entity: CampaignEntity,
    *,
    original_name: str,
    content: bytes,
    mime_type: str | None,
) -> str:
    if entity.entity_type not in ILLUSTRATION_ENTITY_TYPES:
        raise EntityIllustrationError("Tipo de entidad no admite ilustración")
    if len(content) > settings.max_upload_bytes:
        raise EntityIllustrationError(
            f"Imagen demasiado grande (máx. {settings.max_upload_bytes // (1024 * 1024)} MB)"
        )

    suffix = _safe_image_extension(original_name, mime_type)
    illustration_dir = _illustration_dir(entity.campaign_id)
    illustration_dir.mkdir(parents=True, exist_ok=True)

    _delete_existing_illustration_files(entity)
    file_path = illustration_dir / f"{entity.id}{suffix}"
    file_path.write_bytes(content)

    url = illustration_api_path(entity.id)
    write_entity_illustration_url(entity, url)
    await db.commit()
    await db.refresh(entity)
    return url


async def clear_entity_illustration_file(db: AsyncSession, entity: CampaignEntity) -> None:
    _delete_existing_illustration_files(entity)
    write_entity_illustration_url(entity, None)
    await db.commit()
    await db.refresh(entity)
