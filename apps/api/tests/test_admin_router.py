"""Tests for the admin-only introspection endpoints (app/routers/admin.py).

Exercises the require_admin RBAC gate via FastAPI dependency_overrides
(rather than AUTH_DEV_BYPASS, which always grants admin) so each test
controls its own role precisely, plus /admin/audit-logs' org-scoping: since
'admin' is an org-scoped Clerk role (any org can have its own admin), the
endpoint must never return another organization's audit log rows.
"""

from __future__ import annotations

from datetime import UTC, datetime

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.main import app
from app.models.org import AuditLog, Organization


def _user(role: str, org_id: str | None = "test-org") -> CurrentUser:
    return CurrentUser(user_id="test-user", org_id=org_id, role=role, email="test@example.com")


async def test_admin_sources_requires_admin_role(client: AsyncClient) -> None:
    app.dependency_overrides[get_current_user] = lambda: _user("member")
    try:
        response = await client.get("/admin/sources")
    finally:
        app.dependency_overrides.pop(get_current_user, None)
    assert response.status_code == 403


async def test_admin_sources_allows_admin_role(client: AsyncClient) -> None:
    app.dependency_overrides[get_current_user] = lambda: _user("admin")
    try:
        response = await client.get("/admin/sources")
    finally:
        app.dependency_overrides.pop(get_current_user, None)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_admin_audit_logs_unauthenticated_is_401(client: AsyncClient) -> None:
    response = await client.get("/admin/audit-logs")
    assert response.status_code == 401


async def test_admin_audit_logs_no_org_context_returns_empty_page(client: AsyncClient) -> None:
    app.dependency_overrides[get_current_user] = lambda: _user("admin", org_id=None)
    try:
        response = await client.get("/admin/audit-logs")
    finally:
        app.dependency_overrides.pop(get_current_user, None)
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 0


async def test_admin_audit_logs_unprovisioned_org_returns_empty_page(client: AsyncClient) -> None:
    """A Clerk org that has never been mirrored into `organizations` (see
    app/core/provisioning.py) has no audit log rows it could own."""
    app.dependency_overrides[get_current_user] = lambda: _user("admin", org_id="org-never-seen")
    try:
        response = await client.get("/admin/audit-logs")
    finally:
        app.dependency_overrides.pop(get_current_user, None)
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 0


async def test_admin_audit_logs_only_returns_callers_own_org(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Regression test for a cross-tenant leak: a malicious or buggy client
    must not be able to read another organization's audit log."""
    org_a = Organization(clerk_org_id="org-a", name="Org A", slug="org-a")
    org_b = Organization(clerk_org_id="org-b", name="Org B", slug="org-b")
    db_session.add_all([org_a, org_b])
    await db_session.flush()

    db_session.add_all(
        [
            AuditLog(
                organization_id=org_a.id,
                actor_user_id=None,
                action="org_a.action",
                resource_type="test",
                occurred_at=datetime.now(UTC),
            ),
            AuditLog(
                organization_id=org_b.id,
                actor_user_id=None,
                action="org_b.action",
                resource_type="test",
                occurred_at=datetime.now(UTC),
            ),
        ]
    )
    await db_session.commit()

    app.dependency_overrides[get_current_user] = lambda: _user("admin", org_id="org-a")
    try:
        response = await client.get("/admin/audit-logs")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert [item["action"] for item in body["items"]] == ["org_a.action"]


async def test_admin_ingestion_runs_allows_admin_role(client: AsyncClient) -> None:
    app.dependency_overrides[get_current_user] = lambda: _user("admin")
    try:
        response = await client.get("/admin/ingestion-runs")
    finally:
        app.dependency_overrides.pop(get_current_user, None)
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 0
