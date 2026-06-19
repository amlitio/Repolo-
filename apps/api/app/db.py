"""Async SQLAlchemy engine/session setup.

Production/dev uses Postgres+PostGIS via asyncpg (DATABASE_URL=postgresql+asyncpg://...).
The test suite defaults to SQLite via aiosqlite so it never requires a live
Postgres instance. Tables that use PostGIS geometry or pgvector columns are
isolated in app/models/geo.py-derived modules behind types that degrade
gracefully outside Postgres (see app/models/types.py) so most unit tests never
touch a real geometry/vector column.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool

from app.config import get_settings


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


def _make_engine():
    settings = get_settings()
    connect_args = {}
    engine_kwargs = {}
    if settings.database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        if ":memory:" in settings.database_url:
            # In-memory SQLite only persists for the lifetime of a single
            # connection; pin the engine to one shared connection via
            # StaticPool so multiple sessions in the same process (e.g.
            # across test fixtures) see the same database.
            engine_kwargs["poolclass"] = StaticPool
    return create_async_engine(
        settings.database_url, echo=False, connect_args=connect_args, **engine_kwargs
    )


engine = _make_engine()
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a request-scoped async session."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_models() -> None:
    """Create all tables. Used by tests (SQLite) and local bootstrap; production
    schema changes should go through Alembic migrations instead."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
