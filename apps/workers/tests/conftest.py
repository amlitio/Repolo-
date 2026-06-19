"""Shared pytest fixtures for the apps/workers test suite.

Mirrors apps/api/tests/conftest.py: forces DATABASE_URL to an in-memory
SQLite database before any `app.*`/`worker.*` module is imported, so this
suite never requires a live Postgres instance. apps/workers imports
app.db/app.models/app.core.registry directly (apps/api installed as an
editable package - see requirements.txt), so the same Base.metadata is used.
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("AUTH_DEV_BYPASS", "0")
os.environ.setdefault("RUN_LIVE_SMOKE_TESTS", "0")

import asyncio  # noqa: E402
from collections.abc import AsyncIterator  # noqa: E402

import app.models  # noqa: E402,F401
import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from app.db import AsyncSessionLocal, engine, init_models  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402


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


@pytest.fixture(scope="session", autouse=True)
def _dispose_engine_at_end():
    yield
    asyncio.run(engine.dispose())
