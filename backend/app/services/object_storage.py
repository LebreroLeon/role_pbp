"""Object storage abstraction for campaign uploads (local filesystem or Cloudflare R2)."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from app.core.config import settings

IMAGE_MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}

ALLOWED_EXTENSIONS = set(IMAGE_MEDIA_TYPES.keys())


class StorageNotFoundError(FileNotFoundError):
    def __init__(self, key: str) -> None:
        super().__init__(f"Object not found: {key}")
        self.key = key


class StorageBackend(ABC):
    @abstractmethod
    def put_object(self, key: str, content: bytes, content_type: str | None = None) -> None: ...

    @abstractmethod
    def get_object(self, key: str) -> bytes: ...

    @abstractmethod
    def delete_object(self, key: str) -> None: ...

    @abstractmethod
    def exists(self, key: str) -> bool: ...


def avatar_storage_key(campaign_id: uuid.UUID, entity_id: uuid.UUID, extension: str) -> str:
    normalized = ".jpg" if extension == ".jpeg" else extension
    return f"{campaign_id}/avatars/{entity_id}{normalized}"


def illustration_storage_key(campaign_id: uuid.UUID, entity_id: uuid.UUID, extension: str) -> str:
    normalized = ".jpg" if extension == ".jpeg" else extension
    return f"{campaign_id}/illustrations/{entity_id}{normalized}"


def chat_message_image_storage_key(
    campaign_id: uuid.UUID, image_id: uuid.UUID, extension: str
) -> str:
    normalized = ".jpg" if extension == ".jpeg" else extension
    return f"{campaign_id}/chat/{image_id}{normalized}"


def document_storage_key(campaign_id: uuid.UUID, document_id: uuid.UUID, extension: str) -> str:
    return f"{campaign_id}/documents/{document_id}{extension}"


def media_type_for_extension(extension: str) -> str:
    normalized = extension.lower()
    if normalized == ".jpeg":
        normalized = ".jpg"
    return IMAGE_MEDIA_TYPES.get(normalized, "application/octet-stream")


class LocalStorageBackend(StorageBackend):
    def __init__(self, root: Path | None = None) -> None:
        self._root = root or Path(settings.upload_dir)
        self._root.mkdir(parents=True, exist_ok=True)

    def _path_for_key(self, key: str) -> Path:
        return self._root / key

    def put_object(self, key: str, content: bytes, content_type: str | None = None) -> None:
        path = self._path_for_key(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def get_object(self, key: str) -> bytes:
        path = self._path_for_key(key)
        if not path.is_file():
            raise StorageNotFoundError(key)
        return path.read_bytes()

    def delete_object(self, key: str) -> None:
        path = self._path_for_key(key)
        if path.is_file():
            path.unlink()

    def exists(self, key: str) -> bool:
        return self._path_for_key(key).is_file()


class R2StorageBackend(StorageBackend):
    def __init__(self) -> None:
        if not settings.r2_account_id:
            raise ValueError("R2_ACCOUNT_ID is required when STORAGE_BACKEND=r2")
        if not settings.r2_access_key_id or not settings.r2_secret_access_key:
            raise ValueError("R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY are required when STORAGE_BACKEND=r2")
        if not settings.r2_bucket_name:
            raise ValueError("R2_BUCKET_NAME is required when STORAGE_BACKEND=r2")

        import boto3
        from botocore.config import Config

        self._bucket = settings.r2_bucket_name
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.r2_endpoint_url,
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            region_name="auto",
            config=Config(signature_version="s3v4"),
        )

    def put_object(self, key: str, content: bytes, content_type: str | None = None) -> None:
        extra_args: dict[str, str] = {}
        if content_type:
            extra_args["ContentType"] = content_type
        self._client.put_object(Bucket=self._bucket, Key=key, Body=content, **extra_args)

    def get_object(self, key: str) -> bytes:
        from botocore.exceptions import ClientError

        try:
            response = self._client.get_object(Bucket=self._bucket, Key=key)
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")
            if error_code in {"404", "NoSuchKey", "NotFound"}:
                raise StorageNotFoundError(key) from exc
            raise
        return response["Body"].read()

    def delete_object(self, key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=key)

    def exists(self, key: str) -> bool:
        from botocore.exceptions import ClientError

        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")
            if error_code in {"404", "NoSuchKey", "NotFound"}:
                return False
            raise
        return True


def get_storage_backend() -> StorageBackend:
    backend = settings.storage_backend.strip().lower()
    if backend == "r2":
        return R2StorageBackend()
    if backend == "local":
        return LocalStorageBackend()
    raise ValueError(f"Unknown STORAGE_BACKEND: {settings.storage_backend!r} (expected 'local' or 'r2')")


def find_existing_image_key(
    storage: StorageBackend,
    *,
    campaign_id: uuid.UUID,
    entity_id: uuid.UUID,
    category: str,
    allowed_extensions: set[str],
) -> tuple[str, str] | None:
    """Return (storage_key, media_type) for the first matching extension, or None."""
    for suffix in allowed_extensions:
        normalized = ".jpg" if suffix == ".jpeg" else suffix
        if category == "avatars":
            key = avatar_storage_key(campaign_id, entity_id, normalized)
        elif category == "illustrations":
            key = illustration_storage_key(campaign_id, entity_id, normalized)
        else:
            raise ValueError(f"Unknown image category: {category}")
        if storage.exists(key):
            return key, media_type_for_extension(normalized)
    return None
