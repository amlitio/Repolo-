"""Admin-only introspection endpoints: source catalog/status, ingestion run
history, and audit log. All require role='admin' (see app/core/auth.py
require_admin)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, require_admin
from app.core.registry import get_registry
from app.db import get_db
from app.models.admin import SourceRun as SourceRunModel
from app.models.org import AuditLog as AuditLogModel
from app.models.org import Organization
from app.schemas.admin import AuditLogEntry, SourceRun
from app.schemas.common import Paginated
from app.schemas.registry import SourceRegistryEntry

router = APIRouter(tags=["admin"])


@router.get(
    "/admin/sources",
    response_model=list[SourceRegistryEntry],
    summary="List the data source registry with live DB status overrides",
    description="Returns every source from packages/shared/data/sources.json. This is the "
    "static registry only; live last-run status is available via /admin/ingestion-runs.",
)
async def list_sources(
    _current_user: CurrentUser = Depends(require_admin),
) -> list[SourceRegistryEntry]:
    registry = get_registry()
    return [SourceRegistryEntry(**s) for s in registry.sources]


@router.get(
    "/admin/ingestion-runs",
    response_model=Paginated[SourceRun],
    summary="List ingestion (connector) run history",
    description="Returns persisted source_runs rows recorded by apps/workers. Empty until the "
    "worker scheduler has executed at least one ingestion job.",
)
async def list_ingestion_runs(
    _current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    source_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
) -> Paginated[SourceRun]:
    stmt = select(SourceRunModel)
    if source_id:
        stmt = stmt.where(SourceRunModel.source_id == source_id)
    stmt = stmt.order_by(SourceRunModel.started_at.desc())
    result = await db.execute(stmt)
    rows = result.scalars().all()
    total = len(rows)
    start = (page - 1) * page_size
    page_items = rows[start : start + page_size]
    return Paginated[SourceRun](
        items=[
            SourceRun(
                id=r.id,
                source_id=r.source_id,
                status=r.status,
                started_at=r.started_at,
                finished_at=r.finished_at,
                records_fetched=r.records_fetched,
                records_normalized=r.records_normalized,
                error_message=r.error_message,
            )
            for r in page_items
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/admin/audit-logs",
    response_model=Paginated[AuditLogEntry],
    summary="List audit log entries",
    description="Scoped to the caller's own organization. 'admin' (see "
    "app/core/auth.py require_admin) is an org-scoped Clerk role, not a "
    "platform superuser, so this must never accept a caller-supplied "
    "organization id - doing so would let any org's admin read another "
    "org's audit log.",
)
async def list_audit_logs(
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    action: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> Paginated[AuditLogEntry]:
    org_id: str | None = None
    if current_user.org_id:
        org_result = await db.execute(
            select(Organization.id).where(Organization.clerk_org_id == current_user.org_id)
        )
        org_id = org_result.scalar_one_or_none()

    if org_id is None:
        # No org context on this Clerk session, or it has never been
        # provisioned internally (see app/core/provisioning.py) - there is
        # no tenant to scope to, so there is nothing this caller can see.
        return Paginated[AuditLogEntry](items=[], total=0, page=page, page_size=page_size)

    stmt = select(AuditLogModel).where(AuditLogModel.organization_id == org_id)
    if action:
        stmt = stmt.where(AuditLogModel.action == action)
    stmt = stmt.order_by(AuditLogModel.occurred_at.desc())
    result = await db.execute(stmt)
    rows = result.scalars().all()
    total = len(rows)
    start = (page - 1) * page_size
    page_items = rows[start : start + page_size]
    return Paginated[AuditLogEntry](
        items=[
            AuditLogEntry(
                id=r.id,
                actor_user_id=r.actor_user_id,
                organization_id=r.organization_id,
                action=r.action,
                resource_type=r.resource_type,
                resource_id=r.resource_id,
                occurred_at=r.occurred_at,
            )
            for r in page_items
        ],
        total=total,
        page=page,
        page_size=page_size,
    )
