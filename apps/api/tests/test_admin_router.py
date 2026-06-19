"""Tests for the admin-only introspection endpoints (app/routers/admin.py).

Exercises the require_admin RBAC gate via FastAPI dependency_overrides
(rather than AUTH_DEV_BYPASS, which always grants admin) so each test
controls its own role precisely, plus the malformed-organization_id guard
that returns an empty page instead of letting GUID.process_bind_param raise.
"""

from __future__ import annotations

from httpx import AsyncClient

from app.core.auth import CurrentUser, get_current_user
from app.main import app


def _user(role: str) -> CurrentUser:
    return CurrentUser(user_id="test-user", org_id="test-org", role=role, email="test@example.com")


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


async def test_admin_audit_logs_malformed_organization_id_returns_empty_page(
    client: AsyncClient,
) -> None:
    app.dependency_overrides[get_current_user] = lambda: _user("admin")
    try:
        response = await client.get("/admin/audit-logs", params={"organization_id": "not-a-uuid"})
    finally:
        app.dependency_overrides.pop(get_current_user, None)
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 0


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
