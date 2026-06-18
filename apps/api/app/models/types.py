"""Portable column types for geometry/vector data.

GeoAlchemy2's Geometry type and pgvector's Vector type both require Postgres
extensions (PostGIS / pgvector) to create real columns. To keep the bulk of
the unit-test suite running against plain SQLite (no Postgres available in
this sandbox), we wrap both in dialect-aware TypeDecorators: on Postgres they
delegate to the real PostGIS/pgvector types; on every other dialect (sqlite)
they degrade to a TEXT/JSON-serializable column so `CREATE TABLE` and basic
round-trip storage still work for tables that incidentally have a geometry or
vector column but aren't the focus of a given unit test.

Tables that are fundamentally about geometry/vector storage (gis_features,
geographies, embeddings) are exercised only by tests marked
`@pytest.mark.integration` against real Postgres+PostGIS, per the project's
testing constraints.
"""

from __future__ import annotations

import json
import uuid

from geoalchemy2 import Geometry as _PostGISGeometry
from pgvector.sqlalchemy import Vector as _PgVector
from sqlalchemy.dialects.postgresql import UUID as _PostgresUUID
from sqlalchemy.types import CHAR, JSON, TypeDecorator, UserDefinedType


class GUID(TypeDecorator):
    """Platform-independent UUID column.

    Uses Postgres' native UUID type when available, otherwise stores as a
    36-character string (SQLite in unit tests). Always exchanges values as
    `uuid.UUID` / `str` at the Python layer.
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(_PostgresUUID(as_uuid=False))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(uuid.UUID(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return str(value)


class PortableGeometry(UserDefinedType):
    """Geometry column that is a real PostGIS geometry on Postgres and a
    GeoJSON-serialized TEXT column elsewhere (e.g. SQLite in unit tests)."""

    cache_ok = True

    def __init__(self, geometry_type: str = "GEOMETRY", srid: int = 4326) -> None:
        self.geometry_type = geometry_type
        self.srid = srid

    def get_col_spec(self, **kw):  # pragma: no cover - only used outside Postgres
        return "TEXT"

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(_PostGISGeometry(geometry_type=self.geometry_type, srid=self.srid))
        return dialect.type_descriptor(JSON())

    def bind_processor(self, dialect):
        if dialect.name == "postgresql":
            return None

        def process(value):
            if value is None:
                return None
            return value if isinstance(value, str) else json.dumps(value)

        return process

    def result_processor(self, dialect, coltype):
        if dialect.name == "postgresql":
            return None

        def process(value):
            if value is None:
                return None
            try:
                return json.loads(value)
            except (TypeError, ValueError):
                return value

        return process


class PortableVector(TypeDecorator):
    """pgvector Vector column on Postgres; JSON list-of-floats elsewhere."""

    impl = JSON
    cache_ok = True

    def __init__(self, dim: int = 1536, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.dim = dim

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(_PgVector(self.dim))
        return dialect.type_descriptor(JSON())
