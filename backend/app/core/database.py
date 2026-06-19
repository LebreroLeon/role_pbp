from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings
from app.core.db_url import prepare_asyncpg_url


class Base(DeclarativeBase):
    pass


def create_db_engine(*, echo: bool | None = None) -> AsyncEngine:
    url, connect_args = prepare_asyncpg_url(settings.database_url)
    return create_async_engine(
        url,
        echo=settings.app_debug if echo is None else echo,
        connect_args=connect_args,
    )


engine = create_db_engine()
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
