"""
Database engine and session factory.

Supports SQLite (default, via aiosqlite) and PostgreSQL (via asyncpg).
Switch by changing DATABASE_URL in .env — zero code changes required.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

# SQLite requires check_same_thread=False; postgres ignores it harmlessly
connect_args = {"check_same_thread": False} if settings.is_sqlite else {}

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    connect_args=connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """All ORM models inherit from this."""
    pass


async def create_all_tables() -> None:
    """Create all tables — called on app startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields a DB session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
