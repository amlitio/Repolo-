"""Tests for DataDiscoveryAgent: live reachability checks against the 8
partially_verified county GIS URLs already in the registry, the HEAD->GET
fallback, and the aggregate needs_verification backlog DataQualityEvent.
Network calls are respx-mocked; no real HTTP requests are made.
"""

from __future__ import annotations

import pytest
import respx
from app.core.registry import get_registry
from app.models.admin import DataQualityEvent
from httpx import Response
from sqlalchemy import select

from worker.agents.data_discovery_agent import DataDiscoveryAgent


def _partially_verified_urls() -> dict[str, str]:
    registry = get_registry()
    return {
        c["fips"]: c["gis_open_data_url"]
        for c in registry.counties
        if c["data_quality_status"] == "partially_verified" and c["gis_open_data_url"]
    }


@pytest.mark.asyncio
async def test_all_reachable_urls_report_success_and_logs_backlog_event(db_session):
    urls = _partially_verified_urls()
    assert len(urls) == 8  # docs/data-sources/README.md: 8 partially_verified FL counties

    with respx.mock:
        for url in urls.values():
            respx.head(url).mock(return_value=Response(200))

        result = await DataDiscoveryAgent().run(db_session)

    assert result.status == "success"
    assert len(result.details["county_checks"]) == 8
    assert all(c["reachable"] for c in result.details["county_checks"].values())
    assert result.details["needs_verification_count"] == 59

    events = (await db_session.execute(select(DataQualityEvent))).scalars().all()
    assert any(e.severity == "info" and "59 of 67" in e.message for e in events)


@pytest.mark.asyncio
async def test_unreachable_url_marks_partial_and_logs_warning(db_session):
    urls = _partially_verified_urls()
    broken_fips, broken_url = next(iter(urls.items()))

    with respx.mock:
        for fips, url in urls.items():
            status = 500 if fips == broken_fips else 200
            respx.head(url).mock(return_value=Response(status))
            if fips == broken_fips:
                respx.get(url).mock(return_value=Response(status))  # GET fallback also fails

        result = await DataDiscoveryAgent().run(db_session)

    assert result.status == "partial"
    assert result.details["county_checks"][broken_fips]["reachable"] is False
    assert "error" in result.details["county_checks"][broken_fips]

    events = (await db_session.execute(select(DataQualityEvent))).scalars().all()
    assert any(e.severity == "warning" and broken_url in e.message for e in events)


@pytest.mark.asyncio
async def test_head_403_falls_back_to_get_before_marking_unreachable(db_session):
    urls = _partially_verified_urls()
    target_fips, target_url = next(iter(urls.items()))

    with respx.mock:
        for fips, url in urls.items():
            if fips == target_fips:
                respx.head(url).mock(return_value=Response(403))
                respx.get(url).mock(return_value=Response(200))
            else:
                respx.head(url).mock(return_value=Response(200))

        result = await DataDiscoveryAgent().run(db_session)

    assert result.status == "success"
    assert result.details["county_checks"][target_fips]["reachable"] is True


@pytest.mark.asyncio
async def test_no_url_is_fabricated_for_needs_verification_counties(db_session):
    urls = _partially_verified_urls()
    with respx.mock:
        for url in urls.values():
            respx.head(url).mock(return_value=Response(200))
        result = await DataDiscoveryAgent().run(db_session)

    registry = get_registry()
    needs_verification_fips = {
        c["fips"] for c in registry.counties if c["data_quality_status"] == "needs_verification"
    }
    assert set(result.details["needs_verification_fips"]) == needs_verification_fips
    # None of those fips were live-checked - no URL exists for them to check.
    assert needs_verification_fips.isdisjoint(result.details["county_checks"].keys())
