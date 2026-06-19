"""Alembic migration environment.

Runs against the same DATABASE_URL the API itself uses (app.config.Settings),
so there is exactly one source of truth for "what database am I talking to" -
never a second hand-maintained connection string in alembic.ini.

Async because app.db uses an async engine (asyncpg in production, aiosqlite
in tests); see https://alembic.sqlalchemy.org/en/latest/cookbook.html#using-asyncio-with-alembic.

GeoAlchemy2's `include_object`/`render_item` are wired into autogenerate so
the PostGIS-managed `spatial_ref_sys` table is never picked up as a stray
"missing" table, and `Geometry(...)` columns render correctly in generated
migration scripts instead of as opaque `sa.NullType()`.
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from geoalchemy2.alembic_helpers import include_object, render_item
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

import app.models  # noqa: F401 - importing registers every model on Base.metadata
from alembic import context
from app.config import get_settings
from app.db import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    return get_settings().database_url


def run_migrations_offline() -> None:
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        render_item=render_item,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
        render_item=render_item,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = create_async_engine(get_url())
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
