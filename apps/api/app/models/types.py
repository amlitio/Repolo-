"""Portable column types for geometry/vector data.

GeoAlchemy2's Geometry type and pgvector's Vector type both require Postgres
extensions (PostGIS / pgvector) to create real columns. To keep the bulk of
the unit-test suite running against plain SQLite (no Postgres available in
this sandbox), we wrap both in dialect-aware TypeDecorators: on Postgres they
delegate to the real PostGIS/pgvector types (verified against a live
Postgres+PostGIS+pgvector instance via
`alembic/versions/181ea66c4f40_initial_schema.py`); on every other dialect
(sqlite) they degrade to a JSON column so `CREATE TABLE` and basic
round-trip storage still work for tables that incidentally have a geometry or
vector column but aren't the focus of a given unit test.

Tables that are fundamentally about geometry/vector storage (gis_features,
geographies, embeddings) are exercised only by tests marked
`@pytest.mark.integration` against real Postgres+PostGIS, per the project's
testing constraints.
"""

from __future__ import annotations

import uuid

from geoalchemy2 import Geometry as _PostGISGeometry
from pgvector.sqlalchemy import Vector as _PgVector
from sqlalchemy.dialects.postgresql import UUID as _PostgresUUID
from sqlalchemy.types import CHAR, JSON, TypeDecorator


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


def is_valid_guid(value: str | None) -> bool:
    """True if `value` is a syntactically valid UUID string.

    Routers that accept a client-supplied id for a GUID-typed column (e.g.
    `property_id` as a query param) should check this BEFORE querying:
    GUID.process_bind_param raises ValueError on malformed input, which
    would otherwise surface as an unhandled 500 instead of a clean 404 for
    something as ordinary as a typo'd id.
    """
    if not value:
        return False
    try:
        uuid.UUID(value)
    except (ValueError, AttributeError, TypeError):
        return False
    return True


class PortableGeometry(TypeDecorator):
    """Geometry column that is a real PostGIS geometry on Postgres and a
    GeoJSON-shaped JSON column elsewhere (e.g. SQLite in unit tests).

    Mirrors `PortableVector` below rather than using a bare
    `UserDefinedType`: `UserDefinedType.get_col_spec()` has no reliable
    per-dialect hook, so a previous version of this type emitted bare
    `TEXT` columns on Postgres too, silently breaking every spatial query
    (ST_Intersects, bbox search) the map relies on.
    `TypeDecorator.load_dialect_impl()` is what actually drives DDL column
    type resolution per dialect, and embedding a real `Geometry()`/`Vector()`
    instance directly (e.g. via `with_variant()`) also isn't safe here:
    GeoAlchemy2 attaches `Table`-level DDL event listeners (legacy
    `AddGeometryColumn`/`RecoverGeometryColumn` SpatiaLite management calls)
    to any column whose type is an actual `Geometry` instance, which fire
    even on plain SQLite (no SpatiaLite extension loaded) and crash table
    creation in tests. Wrapping it in `TypeDecorator` avoids that entirely.
    """

    impl = JSON
    cache_ok = True

    def __init__(self, geometry_type: str = "GEOMETRY", srid: int = 4326, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.geometry_type = geometry_type
        self.srid = srid
        # A real Geometry instance to delegate attribute lookups to (see
        # __getattr__ below) - never used directly as a column type.
        self._postgis_geometry = _PostGISGeometry(geometry_type=geometry_type, srid=srid)

    def load_dialect_impl(self, dialect):
        # GeoAlchemy2's check_management() probes arbitrary TypeDecorator
        # columns with dialect=None to test whether they wrap a Raster type
        # (geoalchemy2/admin/dialects/common.py:_check_spatial_type). dialect
        # has no .type_descriptor() either in that case, so short-circuit to
        # a bare JSON() instance rather than crashing on dialect.name.
        if dialect is None:
            return JSON()
        if dialect.name == "postgresql":
            return dialect.type_descriptor(self._postgis_geometry)
        return dialect.type_descriptor(JSON())

    def __getattr__(self, key):
        # GeoAlchemy2's Table/Column DDL event listeners (spatial index
        # creation - see geoalchemy2/admin/dialects/postgresql.py
        # after_create/before_create) read Geometry-specific attributes
        # (spatial_index, use_typmod, dimension, srid, geometry_type)
        # straight off `column.type`, without a dialect context and without
        # an attribute-error-tolerant getattr() default in every call site.
        # TypeDecorator's own __getattr__ proxies to self.impl_instance,
        # which is always the generic JSON() impl (never the dialect-
        # resolved Geometry), so those reads would otherwise raise
        # AttributeError even on Postgres. Proxy to the real Geometry
        # instance instead, which has the correct values for both.
        return getattr(self._postgis_geometry, key)

    def __repr__(self) -> str:
        # TypeDecorator.__repr__ inspects self.impl_instance (JSON) by
        # default, which has no geometry_type/srid params - Alembic
        # autogenerate calls repr() to render this type into migration
        # scripts, so without this override every generated geometry column
        # would silently fall back to the generic_type/srid defaults.
        return f"PortableGeometry(geometry_type={self.geometry_type!r}, srid={self.srid!r})"


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

    def __repr__(self) -> str:
        return f"PortableVector(dim={self.dim!r})"
