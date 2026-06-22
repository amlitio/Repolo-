"""Weather alerts and hurricane tracks (NWS, NHC)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.mixins import TimestampMixin, new_uuid
from app.models.types import GUID, PortableGeometry


class WeatherAlert(Base, TimestampMixin):
    """Mirrors packages/shared/src/types/api.ts::WeatherAlert."""

    __tablename__ = "weather_alerts"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=new_uuid)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    event: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    certainty: Mapped[str] = mapped_column(String(50), nullable=False)
    urgency: Mapped[str] = mapped_column(String(50), nullable=False)
    headline: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    area_desc: Mapped[str] = mapped_column(Text, nullable=False)
    county_fips_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    effective_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_id: Mapped[str] = mapped_column(String(100), ForeignKey("sources.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)


class HurricaneTrack(Base, TimestampMixin):
    """Mirrors packages/shared/src/types/api.ts::HurricaneTrack."""

    __tablename__ = "hurricane_tracks"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=new_uuid)
    storm_id: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    season: Mapped[int] = mapped_column(Integer, nullable=False)
    advisory_num: Mapped[str] = mapped_column(String(50), nullable=False)
    classification: Mapped[str] = mapped_column(String(100), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    geometry = mapped_column(PortableGeometry(geometry_type="GEOMETRY", srid=4326), nullable=True)
