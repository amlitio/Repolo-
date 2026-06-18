"""Procurement opportunities, projects, funding sources, opportunity scoring.

These tables are scaffolded ahead of the ingestion pipeline that will
populate them (SAM.gov, Grants.gov, MyFloridaMarketPlace) - see
sources.json categories "procurement"/"grants" and the procurement_agent.py
scaffold in apps/workers. Endpoints document this as "ingestion pending".
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.mixins import TimestampMixin, new_uuid
from app.models.types import GUID


class ProcurementOpportunity(Base, TimestampMixin):
    __tablename__ = "procurement_opportunities"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=new_uuid)
    source_id: Mapped[str] = mapped_column(String(100), ForeignKey("sources.id"), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    agency: Mapped[str | None] = mapped_column(String(255), nullable=True)
    county_fips: Mapped[str | None] = mapped_column(String(5), nullable=True)
    posted_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    response_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class Project(Base, TimestampMixin):
    """Scaffold for tracked mitigation/infrastructure projects (rank-able
    opportunities). Populated by future ingestion, not the MVP scope."""

    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=new_uuid)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    county_fips: Mapped[str | None] = mapped_column(String(5), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="scaffold")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class FundingSource(Base, TimestampMixin):
    __tablename__ = "funding_sources"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=new_uuid)
    project_id: Mapped[str | None] = mapped_column(GUID(), ForeignKey("projects.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    program: Mapped[str | None] = mapped_column(String(255), nullable=True)
    amount: Mapped[float | None] = mapped_column(Float, nullable=True)


class OpportunityScore(Base, TimestampMixin):
    """Scaffold ranking score for a procurement opportunity / project; not
    yet computed in this MVP (see GET /opportunities/rank)."""

    __tablename__ = "opportunity_scores"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=new_uuid)
    opportunity_id: Mapped[str | None] = mapped_column(
        GUID(), ForeignKey("procurement_opportunities.id"), nullable=True
    )
    project_id: Mapped[str | None] = mapped_column(GUID(), ForeignKey("projects.id"), nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
