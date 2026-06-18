"""Generic, normalized alert records used by the subscription/notification
system.

This is distinct from `weather_alerts` (the raw NWS alert feed mirrored in
app/models/weather.py): `Alert` is the normalized, source-agnostic record
the alerting/subscription pipeline reasons over (it can originate from a
weather alert, a risk-score change, a new flood zone revision, etc.) and is
what GET /alerts serves to clients alongside (or instead of) raw weather
alerts.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.mixins import TimestampMixin, new_uuid
from app.models.types import GUID


class Alert(Base, TimestampMixin):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=new_uuid)
    alert_type: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "weather", "risk_change"
    county_fips: Mapped[str | None] = mapped_column(String(5), nullable=True)
    property_id: Mapped[str | None] = mapped_column(GUID(), nullable=True)
    severity: Mapped[str] = mapped_column(String(50), nullable=False, default="Unknown")
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    origin_source_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    effective_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
