"""Data Discovery agent.

Checks the health of the Florida county data registry
(packages/shared/data/counties.json) and surfaces the verification backlog
as DataQualityEvents - never invents a URL for a county that doesn't have
one yet.

docs/data-sources/README.md documents that 59 of the 67 counties are
data_quality_status="needs_verification" with every URL field set to null,
and explicitly forbids guessing a URL pattern by extrapolating from the 8
"partially_verified" counties that do have a gis_open_data_url. This agent
respects that constraint: it only ever touches URLs that are already in the
registry.

Each run does two things:
1. Live reachability check (HEAD, falling back to GET) against each
   partially_verified county's gis_open_data_url - catches link rot on URLs
   we already trust. Failures are logged as a DataQualityEvent
   (severity="warning").
2. One aggregate DataQualityEvent (severity="info") recording the size of
   the needs_verification backlog, so it's visible via
   GET /admin/data-quality-events without creating 59 near-duplicate rows.

DataQualityEvent.source_id is a NOT NULL foreign key to sources.id, and FL
counties have no row of their own in sources.json, so every event this
agent raises is attached to "fl-statewide-geospatial-portal" - the source
sources.json itself documents as the right fallback when a county-specific
portal is unavailable or unverified.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx
from app.core.registry import get_registry
from sqlalchemy.ext.asyncio import AsyncSession

from worker.agents.base import Agent, AgentRunResult
from worker.persistence import record_data_quality_event

FALLBACK_SOURCE_ID = "fl-statewide-geospatial-portal"
REQUEST_TIMEOUT = 15.0


async def _check_url_reachable(client: httpx.AsyncClient, url: str) -> tuple[bool, str | None]:
    try:
        response = await client.head(url, follow_redirects=True)
        if response.status_code >= 400:
            # Some county GIS portals reject HEAD; retry with GET before
            # treating the URL as unreachable.
            response = await client.get(url, follow_redirects=True)
        if response.status_code >= 400:
            return False, f"HTTP {response.status_code}"
        return True, None
    except httpx.HTTPError as exc:
        return False, str(exc)


class DataDiscoveryAgent(Agent):
    name = "data_discovery"

    async def execute(self, session: AsyncSession) -> AgentRunResult:
        started_at = datetime.now(UTC)
        registry = get_registry()
        counties = registry.counties

        partially_verified = [
            c for c in counties if c["data_quality_status"] == "partially_verified" and c["gis_open_data_url"]
        ]
        needs_verification = [c for c in counties if c["data_quality_status"] == "needs_verification"]

        county_checks: dict[str, Any] = {}
        unreachable = 0
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            for county in partially_verified:
                url = county["gis_open_data_url"]
                ok, error = await _check_url_reachable(client, url)
                county_checks[county["fips"]] = {"name": county["name"], "url": url, "reachable": ok}
                if not ok:
                    unreachable += 1
                    county_checks[county["fips"]]["error"] = error
                    await record_data_quality_event(
                        session,
                        source_id=FALLBACK_SOURCE_ID,
                        severity="warning",
                        message=(
                            f"{county['name']} County gis_open_data_url ({url}) failed "
                            f"reachability check: {error}"
                        ),
                    )

        if needs_verification:
            await record_data_quality_event(
                session,
                source_id=FALLBACK_SOURCE_ID,
                severity="info",
                message=(
                    f"{len(needs_verification)} of {len(counties)} Florida counties remain "
                    "data_quality_status=needs_verification with no registered GIS/procurement/"
                    "permits/parcels URL. No URL has been guessed or extrapolated for any of "
                    "them; manual verification is required before they can be added to "
                    "packages/shared/data/counties.json."
                ),
            )

        finished_at = datetime.now(UTC)
        status = "partial" if unreachable else "success"
        return AgentRunResult(
            agent_name=self.name,
            status=status,
            started_at=started_at,
            finished_at=finished_at,
            summary=(
                f"Checked {len(partially_verified)} partially-verified county URL(s), "
                f"{unreachable} unreachable. {len(needs_verification)} county(ies) remain "
                "needs_verification."
            ),
            details={
                "county_checks": county_checks,
                "needs_verification_count": len(needs_verification),
                "needs_verification_fips": [c["fips"] for c in needs_verification],
            },
        )
