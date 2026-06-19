"""Geographic reference data: geographies, map layers, generic GIS features.

`Geography` and `GisFeature` carry a geometry column (PortableGeometry).
On Postgres this is a real PostGIS geometry; on SQLite (unit tests) it
degrades to a GeoJSON-serialized TEXT/JSON column so CREATE TABLE / basic
CRUD still works, but any test relying on real spatial predicates (ST_*,
bbox intersection at the DB layer) is marked `@pytest.mark.integration`.
"""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.mixins import TimestampMixin, new_uuid
from app.models.types import GUID, PortableGeometry

GeographyKind = str  # "state" | "county" | "city" | "parcel" | "property" | "basin" | "watershed"


class Geography(Base, TimestampMixin):
    """Generic geography record discriminated by `kind`."""

    __tablename__ = "geographies"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=new_uuid)
    kind: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    fips: Mapped[str | None] = mapped_column(String(15), nullable=True)
    parent_id: Mapped[str | None] = mapped_column(GUID(), ForeignKey("geographies.id"), nullable=True)
    geometry = mapped_column(PortableGeometry(geometry_type="GEOMETRY", srid=4326), nullable=True)
    properties_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class MapLayer(Base, TimestampMixin):
    """Mirrors packages/shared/src/types/api.ts::MapLayerDefinition."""

    __tablename__ = "map_layers"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    source_id: Mapped[str] = mapped_column(String(100), nullable=False)
    default_visible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    min_zoom: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_zoom: Mapped[int] = mapped_column(Integer, default=22, nullable=False)
    legend_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")


class LayerVersion(Base, TimestampMixin):
    """A versioned snapshot of a map layer's underlying feature set."""

    __tablename__ = "layer_versions"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=new_uuid)
    layer_id: Mapped[str] = mapped_column(String(100), ForeignKey("map_layers.id"), nullable=False)
    version_label: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class GisFeature(Base, TimestampMixin):
    """Generic geometry + properties JSONB feature, linked to a layer version."""

    __tablename__ = "gis_features"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=new_uuid)
    layer_version_id: Mapped[str] = mapped_column(GUID(), ForeignKey("layer_versions.id"), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    geometry = mapped_column(PortableGeometry(geometry_type="GEOMETRY", srid=4326), nullable=True)
    properties_json: Mapped[str | None] = mapped_column(Text, nullable=True)
