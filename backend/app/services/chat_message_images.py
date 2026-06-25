"""Scene chat message image uploads (master-only)."""

from __future__ import annotations

import re
import uuid
from pathlib import Path

from app.core.config import settings
from app.models.campaign import Scene
from app.services.object_storage import (
    ALLOWED_EXTENSIONS,
    StorageNotFoundError,
    chat_message_image_storage_key,
    get_storage_backend,
    media_type_for_extension,
)

MIME_SUFFIX_MAP = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

MESSAGE_IMAGE_PATH_RE = re.compile(
    r"^/api/v1/scenes/([0-9a-f-]{36})/message-images/([0-9a-f-]{36})$",
    re.IGNORECASE,
)


class ChatMessageImageError(ValueError):
    pass


def message_image_api_path(scene_id: uuid.UUID, image_id: uuid.UUID) -> str:
    return f"/api/v1/scenes/{scene_id}/message-images/{image_id}"


def parse_message_image_url(url: str) -> tuple[uuid.UUID, uuid.UUID] | None:
    match = MESSAGE_IMAGE_PATH_RE.match(url.strip())
    if not match:
        return None
    return uuid.UUID(match.group(1)), uuid.UUID(match.group(2))


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
    raise ChatMessageImageError(
        f"Tipo de imagen no permitido. Permitidos: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
    )


def resolve_scene_message_image_storage(
    scene: Scene,
    image_url: str,
) -> tuple[str, str] | None:
    parsed = parse_message_image_url(image_url)
    if parsed is None:
        return None
    scene_id, image_id = parsed
    if scene_id != scene.id:
        return None

    storage = get_storage_backend()
    for suffix in ALLOWED_EXTENSIONS:
        normalized = ".jpg" if suffix == ".jpeg" else suffix
        key = chat_message_image_storage_key(scene.campaign_id, image_id, normalized)
        if storage.exists(key):
            return key, media_type_for_extension(normalized)
    return None


def validate_message_image_url(scene: Scene, image_url: str) -> None:
    if resolve_scene_message_image_storage(scene, image_url) is None:
        raise ChatMessageImageError("URL de imagen de mensaje no válida o no encontrada")


def save_scene_message_image_file(
    scene: Scene,
    *,
    original_name: str,
    content: bytes,
    mime_type: str | None,
) -> str:
    if len(content) > settings.max_upload_bytes:
        raise ChatMessageImageError(
            f"Imagen demasiado grande (máx. {settings.max_upload_bytes // (1024 * 1024)} MB)"
        )

    image_id = uuid.uuid4()
    suffix = _safe_image_extension(original_name, mime_type)
    storage = get_storage_backend()
    key = chat_message_image_storage_key(scene.campaign_id, image_id, suffix)
    content_type = mime_type or media_type_for_extension(suffix)
    storage.put_object(key, content, content_type=content_type)
    return message_image_api_path(scene.id, image_id)


def get_scene_message_image_bytes(scene: Scene, image_id: uuid.UUID) -> tuple[bytes, str]:
    storage = get_storage_backend()
    for suffix in ALLOWED_EXTENSIONS:
        normalized = ".jpg" if suffix == ".jpeg" else suffix
        key = chat_message_image_storage_key(scene.campaign_id, image_id, normalized)
        try:
            content = storage.get_object(key)
        except StorageNotFoundError:
            continue
        return content, media_type_for_extension(normalized)
    raise ChatMessageImageError("Imagen no encontrada")
