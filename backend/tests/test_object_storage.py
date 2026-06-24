"""Unit tests for object storage backends."""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.core.config import settings
from app.services.object_storage import (
    LocalStorageBackend,
    R2StorageBackend,
    StorageNotFoundError,
    avatar_storage_key,
    get_storage_backend,
)


def test_avatar_storage_key_format():
    campaign_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
    entity_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
    assert avatar_storage_key(campaign_id, entity_id, ".png") == (
        "11111111-1111-1111-1111-111111111111/avatars/22222222-2222-2222-2222-222222222222.png"
    )


def test_local_storage_put_get_delete_exists(tmp_path):
    backend = LocalStorageBackend(root=tmp_path)
    key = "campaign/avatars/entity.png"

    backend.put_object(key, b"image-bytes", content_type="image/png")
    assert backend.exists(key) is True
    assert backend.get_object(key) == b"image-bytes"

    backend.delete_object(key)
    assert backend.exists(key) is False


def test_local_storage_get_missing_raises(tmp_path):
    backend = LocalStorageBackend(root=tmp_path)
    with pytest.raises(StorageNotFoundError):
        backend.get_object("missing/key.png")


def test_get_storage_backend_local_default():
  original = settings.storage_backend
  settings.storage_backend = "local"
  try:
      backend = get_storage_backend()
      assert isinstance(backend, LocalStorageBackend)
  finally:
      settings.storage_backend = original


def test_r2_storage_put_get_delete_exists():
    mock_client = MagicMock()
    mock_body = MagicMock()
    mock_body.read.return_value = b"r2-bytes"
    mock_client.get_object.return_value = {"Body": mock_body}

    with patch("app.services.object_storage.settings") as mock_settings:
        mock_settings.r2_account_id = "acct"
        mock_settings.r2_access_key_id = "key"
        mock_settings.r2_secret_access_key = "secret"
        mock_settings.r2_bucket_name = "rolepbp"
        mock_settings.r2_endpoint_url = "https://acct.r2.cloudflarestorage.com"
        with patch("boto3.client", return_value=mock_client):
            backend = R2StorageBackend()

    key = "camp/avatars/id.png"
    backend.put_object(key, b"r2-bytes", content_type="image/png")
    mock_client.put_object.assert_called_once_with(
        Bucket="rolepbp",
        Key=key,
        Body=b"r2-bytes",
        ContentType="image/png",
    )

    assert backend.get_object(key) == b"r2-bytes"
    mock_client.get_object.assert_called_once_with(Bucket="rolepbp", Key=key)

    backend.delete_object(key)
    mock_client.delete_object.assert_called_once_with(Bucket="rolepbp", Key=key)

    mock_client.head_object.return_value = {}
    assert backend.exists(key) is True


def test_r2_storage_get_missing_raises():
    mock_client = MagicMock()
    error_response = {"Error": {"Code": "NoSuchKey"}}
    mock_client.get_object.side_effect = ClientError(error_response, "GetObject")

    with patch("app.services.object_storage.settings") as mock_settings:
        mock_settings.r2_account_id = "acct"
        mock_settings.r2_access_key_id = "key"
        mock_settings.r2_secret_access_key = "secret"
        mock_settings.r2_bucket_name = "rolepbp"
        mock_settings.r2_endpoint_url = "https://acct.r2.cloudflarestorage.com"
        with patch("boto3.client", return_value=mock_client):
            backend = R2StorageBackend()

    with pytest.raises(StorageNotFoundError):
        backend.get_object("missing.png")


def test_r2_storage_requires_credentials():
    with patch("app.services.object_storage.settings") as mock_settings:
        mock_settings.r2_account_id = ""
        mock_settings.r2_access_key_id = ""
        mock_settings.r2_secret_access_key = ""
        mock_settings.r2_bucket_name = "rolepbp"
        with pytest.raises(ValueError, match="R2_ACCOUNT_ID"):
            R2StorageBackend()
