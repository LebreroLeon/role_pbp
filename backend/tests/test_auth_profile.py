import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from app.models.user import User
from app.schemas.auth import UpdateProfileRequest
from app.services.auth import update_user_profile


def test_update_profile_request_validation():
    UpdateProfileRequest(display_name="Shaw")
    with pytest.raises(ValidationError):
        UpdateProfileRequest(display_name="A")
    with pytest.raises(ValidationError):
        UpdateProfileRequest(display_name="x" * 33)


def test_update_user_profile_trims_and_persists():
    user = User(
        id=uuid.uuid4(),
        email="shaw@example.com",
        password_hash="hash",
        display_name="Old Name",
    )
    db = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    response = asyncio.run(
        update_user_profile(db, user, UpdateProfileRequest(display_name="  Shaw  "))
    )

    assert user.display_name == "Shaw"
    assert response.display_name == "Shaw"
    assert response.email == "shaw@example.com"
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(user)
