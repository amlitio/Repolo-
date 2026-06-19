"""Shared ingestion bookkeeping: sources, source_runs, data_quality_events.

Every connector run an agent performs is recorded here so `GET
/admin/ingestion-runs` is never empty once the scheduler has executed, and
upstream failures show up as DataQualityEvents instead of being silently
dropped - never as fabricated success.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.connectors.base import ConnectorRunResult
from app.models.admin import DataQualityEvent, Source, SourceRun
from app.models.mixins import new_uuid
from sqlalchemy.ext.asyncio import AsyncSession


async def ensure_source_row(session: AsyncSession, source_id: str) -> Source:
    """Idempotently create the DB-side bookkeeping row for a source."""
    existing = await session.get(Source, source_id)
    if existing is not None:
        return existing
    source = Source(id=source_id)
    session.add(source)
    await session.flush()
    return source


async def record_data_quality_event(
    session: AsyncSession,
    *,
    source_id: str,
    severity: str,
    message: str,
    source_run_id: str | None = None,
    detected_at: datetime | None = None,
) -> DataQualityEvent:
    await ensure_source_row(session, source_id)
    event = DataQualityEvent(
        id=new_uuid(),
        source_id=source_id,
        source_run_id=source_run_id,
        severity=severity,
        message=message,
        detected_at=detected_at or datetime.now(UTC),
    )
    session.add(event)
    await session.flush()
    return event


async def record_connector_run(
    session: AsyncSession,
    result: ConnectorRunResult,
    *,
    records_normalized: int | None = None,
) -> SourceRun:
    """Persist a ConnectorRunResult as a source_runs row, and log a
    data_quality_event automatically when the run was not a clean success -
    never silently substituted data for a failed/degraded fetch."""

    await ensure_source_row(session, result.source_id)
    run = SourceRun(
        id=new_uuid(),
        source_id=result.source_id,
        status=result.status,
        started_at=result.started_at,
        finished_at=result.finished_at,
        records_fetched=result.records_fetched,
        records_normalized=(
            records_normalized if records_normalized is not None else result.records_fetched
        ),
        error_message=result.error_message,
    )
    session.add(run)
    await session.flush()

    if result.status in ("failed", "degraded"):
        await record_data_quality_event(
            session,
            source_id=result.source_id,
            severity="error" if result.status == "failed" else "degraded",
            message=result.error_message or f"Connector run reported status={result.status}",
            source_run_id=run.id,
        )
    elif result.status == "success":
        source = await session.get(Source, result.source_id)
        if source is not None:
            source.last_successful_run_at = result.finished_at
            await session.flush()

    return run
