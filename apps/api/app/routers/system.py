"""Health/readiness/version endpoints. Public, no auth, /health never
touches the DB."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_db

router = APIRouter(tags=["system"])


@router.get("/health", summary="Liveness check", description="Always returns ok; never touches the DB.")
async def health() -> dict:
    return {"status": "ok"}


@router.get(
    "/ready",
    summary="Readiness check",
    description="Verifies dependent services (DB) are reachable. Returns 503 if a required check fails.",
)
async def ready(response: Response, db: AsyncSession = Depends(get_db)) -> dict:
    checks: dict[str, str] = {}
    try:
        await db.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception:  # noqa: BLE001
        checks["db"] = "error"

    overall_ok = all(v == "ok" for v in checks.values())
    if not overall_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ready" if overall_ok else "degraded", "checks": checks}


@router.get("/version", summary="Build/version metadata")
async def version() -> dict:
    settings = get_settings()
    return {
        "version": settings.app_version,
        "git_sha": settings.git_sha,
        "build_time": settings.build_time,
    }
