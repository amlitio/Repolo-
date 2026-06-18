"""Shared pytest fixtures for the apps/api test suite.

Forces DATABASE_URL to an in-memory SQLite database before any app module
is imported, so the test suite never requires a live Postgres instance.
Tests that genuinely need PostGIS/pgvector-specific SQL must be marked
`@pytest.mark.integration` and are skipped by default (see pyproject.toml).
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("AUTH_DEV_BYPASS", "0")
os.environ.setdefault("RUN_LIVE_SMOKE_TESTS", "0")

import asyncio  # noqa: E402
from collections.abc import AsyncIterator  # noqa: E402

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.db import AsyncSessionLocal, engine, init_models  # noqa: E402
import app.models  # noqa: E402,F401


@pytest.fixture(scope="session", autouse=True)
def _initialize_schema():
    """Create all tables once per test session against the in-memory sqlite DB."""
    asyncio.run(init_models())
    yield


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="session", autouse=True)
def _dispose_engine_at_end():
    yield
    asyncio.run(engine.dispose())
