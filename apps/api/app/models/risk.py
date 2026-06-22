"""Properties and risk scoring tables."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.mixins import TimestampMixin, new_uuid
from app.models.types import GUID, PortableGeometry


class Property(Base, TimestampMixin):
    __tablename__ = "properties"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=new_uuid)
    address: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    county_fips: Mapped[str | None] = mapped_column(String(5), nullable=True)
    parcel_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    geometry = mapped_column(PortableGeometry(geometry_type="POINT", srid=4326), nullable=True)


class PropertyRiskScore(Base, TimestampMixin):
    """Mirrors packages/shared/src/types/api.ts::PropertyRiskScore."""

    __tablename__ = "property_risk_scores"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=new_uuid)
    property_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    grade: Mapped[str] = mapped_column(String(1), nullable=False)
    factors_json: Mapped[str] = mapped_column(Text, nullable=False)  # JSON-encoded list[RiskFactor]
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CountyRiskScore(Base, TimestampMixin):
    """Mirrors packages/shared/src/types/api.ts::CountyRiskScore."""

    __tablename__ = "county_risk_scores"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=new_uuid)
    county_fips: Mapped[str] = mapped_column(String(5), nullable=False, index=True)
    county_name: Mapped[str] = mapped_column(String(100), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    grade: Mapped[str] = mapped_column(String(1), nullable=False)
    factors_json: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ScoreExplanation(Base, TimestampMixin):
    """Persisted long-form methodology explanation backing /risk/explain,
    decoupled from the (shorter) `explanation` field stored alongside each
    score so the explain endpoint can serve a richer methodology narrative."""

    __tablename__ = "score_explanations"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=new_uuid)
    property_id: Mapped[str | None] = mapped_column(
        GUID(), ForeignKey("properties.id", ondelete="CASCADE"), nullable=True, index=True
    )
    county_fips: Mapped[str | None] = mapped_column(String(5), nullable=True, index=True)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    methodology: Mapped[str] = mapped_column(Text, nullable=False)
    factors_json: Mapped[str] = mapped_column(Text, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
