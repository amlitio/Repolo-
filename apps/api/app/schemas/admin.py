"""Admin schemas: source runs, audit log entries."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SourceRun(BaseModel):
    id: str
    source_id: str
    status: str
    started_at: datetime
    finished_at: datetime | None
    records_fetched: int
    records_normalized: int
    error_message: str | None


class AuditLogEntry(BaseModel):
    id: str
    actor_user_id: str | None
    organization_id: str | None
    action: str
    resource_type: str
    resource_id: str | None
    occurred_at: datetime
