"""Ingestion/admin bookkeeping: sources, source_runs, raw_documents,
normalized_records, data_quality_events.

`Source` mirrors (and DB-overrides) entries from packages/shared/data/sources.json
so we can track live status separately from the static registry file.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.mixins import TimestampMixin, new_uuid
from app.models.types import GUID


class Source(Base, TimestampMixin):
    """DB-side override/status record for a source.json entry.

    `id` matches the string id used in packages/shared/data/sources.json
    (e.g. "fema-nfhl"), NOT a UUID, so the two can always be joined directly.
    """

    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    data_quality_status_override: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_successful_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class SourceRun(Base, TimestampMixin):
    __tablename__ = "source_runs"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=new_uuid)
    source_id: Mapped[str] = mapped_column(String(100), ForeignKey("sources.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # success | partial | failed | degraded
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    records_fetched: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_normalized: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class RawDocument(Base, TimestampMixin):
    """Raw payload captured from a connector fetch, before normalization."""

    __tablename__ = "raw_documents"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=new_uuid)
    source_id: Mapped[str] = mapped_column(String(100), ForeignKey("sources.id"), nullable=False)
    source_run_id: Mapped[str | None] = mapped_column(GUID(), ForeignKey("source_runs.id"), nullable=True)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False, default="application/json")
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class NormalizedRecord(Base, TimestampMixin):
    """A normalized, connector-agnostic representation of a raw document
    entity, prior to being upserted into a domain table."""

    __tablename__ = "normalized_records"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=new_uuid)
    source_id: Mapped[str] = mapped_column(String(100), ForeignKey("sources.id"), nullable=False)
    raw_document_id: Mapped[str | None] = mapped_column(GUID(), ForeignKey("raw_documents.id"), nullable=True)
    record_type: Mapped[str] = mapped_column(String(100), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    data: Mapped[str] = mapped_column(Text, nullable=False)  # JSON-encoded normalized payload


class DataQualityEvent(Base, TimestampMixin):
    __tablename__ = "data_quality_events"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=new_uuid)
    source_id: Mapped[str] = mapped_column(String(100), ForeignKey("sources.id"), nullable=False)
    source_run_id: Mapped[str | None] = mapped_column(GUID(), ForeignKey("source_runs.id"), nullable=True)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)  # info | warning | error | degraded
    message: Mapped[str] = mapped_column(Text, nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
