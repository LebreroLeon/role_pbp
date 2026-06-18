import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UpdateProfileRequest, UserResponse


class AuthServiceError(ValueError):
    pass


async def register_user(db: AsyncSession, payload: RegisterRequest) -> AuthResponse:
    existing = await db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing is not None:
        raise AuthServiceError("Email already registered")

    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        display_name=payload.display_name.strip(),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return _build_auth_response(user)


async def login_user(db: AsyncSession, payload: LoginRequest) -> AuthResponse:
    user = await db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise AuthServiceError("Invalid email or password")

    return _build_auth_response(user)


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await db.scalar(select(User).where(User.id == user_id))


async def update_user_profile(db: AsyncSession, user: User, payload: UpdateProfileRequest) -> UserResponse:
    user.display_name = payload.display_name.strip()
    await db.commit()
    await db.refresh(user)
    return UserResponse(id=str(user.id), email=user.email, display_name=user.display_name)


def _build_auth_response(user: User) -> AuthResponse:
    token = create_access_token(str(user.id))
    return AuthResponse(
        access_token=token,
        user=UserResponse(id=str(user.id), email=user.email, display_name=user.display_name),
    )
