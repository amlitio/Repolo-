"""Audit logging helper used by admin/export/alert/org-change routes."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.org import AuditLog


async def record_audit_log(
    db: AsyncSession,
    *,
    actor_user_id: str | None,
    organization_id: str | None,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    metadata: dict | None = None,
) -> AuditLog:
    """Persist an audit log row. Callers are responsible for committing the
    session (or letting the surrounding request-scoped session commit)."""

    entry = AuditLog(
        actor_user_id=actor_user_id,
        organization_id=organization_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata_json=json.dumps(metadata) if metadata is not None else None,
        occurred_at=datetime.now(UTC),
    )
    db.add(entry)
    await db.flush()
    return entry
