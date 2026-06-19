"""FEMA flood data: flood zones, disaster declarations, mitigation projects,
NFIP claims summaries."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.mixins import TimestampMixin, new_uuid
from app.models.types import GUID, PortableGeometry


class FloodZone(Base, TimestampMixin):
    """Mirrors packages/shared/src/types/api.ts::FloodZone."""

    __tablename__ = "flood_zones"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=new_uuid)
    fips: Mapped[str] = mapped_column(String(5), nullable=False)
    zone_label: Mapped[str] = mapped_column(String(50), nullable=False)
    is_special_flood_hazard_area: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    base_flood_elevation: Mapped[float | None] = mapped_column(Float, nullable=True)
    geometry = mapped_column(PortableGeometry(geometry_type="GEOMETRY", srid=4326), nullable=True)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)


class FemaDisaster(Base, TimestampMixin):
    __tablename__ = "fema_disasters"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=new_uuid)
    disaster_number: Mapped[str] = mapped_column(String(50), nullable=False)
    county_fips: Mapped[str | None] = mapped_column(String(5), nullable=True)
    state: Mapped[str] = mapped_column(String(2), nullable=False, default="FL")
    declaration_type: Mapped[str] = mapped_column(String(50), nullable=False)
    incident_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    declaration_date: Mapped[date] = mapped_column(Date, nullable=False)


class MitigationProject(Base, TimestampMixin):
    __tablename__ = "mitigation_projects"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=new_uuid)
    project_id: Mapped[str] = mapped_column(String(100), nullable=False)
    county_fips: Mapped[str | None] = mapped_column(String(5), nullable=True)
    program: Mapped[str] = mapped_column(String(100), nullable=False)  # BRIC | HMGP | FMA
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    federal_share_obligated: Mapped[float | None] = mapped_column(Float, nullable=True)
    approval_date: Mapped[date | None] = mapped_column(Date, nullable=True)


class NfipClaimsSummary(Base, TimestampMixin):
    """Aggregated NFIP claims stats per county, used as a risk-scoring input."""

    __tablename__ = "nfip_claims_summary"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=new_uuid)
    county_fips: Mapped[str] = mapped_column(String(5), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    total_claims: Mapped[int] = mapped_column(nullable=False, default=0)
    total_claims_paid: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
