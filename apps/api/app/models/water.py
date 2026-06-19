"""Water monitoring stations and observations (USGS, WMD, NOAA CO-OPS)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.mixins import TimestampMixin, new_uuid
from app.models.types import GUID


class WaterStation(Base, TimestampMixin):
    """Mirrors packages/shared/src/types/api.ts::WaterStation."""

    __tablename__ = "water_stations"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=new_uuid)
    source_id: Mapped[str] = mapped_column(String(100), ForeignKey("sources.id"), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    agency: Mapped[str] = mapped_column(String(255), nullable=False)
    county_fips: Mapped[str | None] = mapped_column(String(5), nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    parameter_types_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")


class WaterObservation(Base, TimestampMixin):
    """Mirrors packages/shared/src/types/api.ts::WaterObservation."""

    __tablename__ = "water_observations"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=new_uuid)
    station_id: Mapped[str] = mapped_column(GUID(), ForeignKey("water_stations.id"), nullable=False)
    parameter: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    qualifier: Mapped[str | None] = mapped_column(String(100), nullable=True)
