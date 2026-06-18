"""Tests for the NWS alerts connector, including the required User-Agent header."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import respx
from httpx import Response

from app.connectors.nws_alerts import NwsAlertsConnector

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "nws_alerts_active_fl.json"


def _load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text())


def test_normalize_skips_records_missing_effective_or_expires():
    connector = NwsAlertsConnector()
    records = connector.normalize(_load_fixture())
    # Third fixture record has no effective/expires and must be skipped.
    assert len(records) == 2
    flood_warning = next(r for r in records if r.event == "Flood Warning")
    assert flood_warning.severity == "Severe"
    assert flood_warning.county_fips == ["12086"]


@pytest.mark.asyncio
@respx.mock
async def test_fetch_raw_sends_required_user_agent_header():
    connector = NwsAlertsConnector()
    route = respx.get(url__regex=r".*api\.weather\.gov.*").mock(
        return_value=Response(200, json=_load_fixture())
    )
    await connector.fetch_raw(area="FL")
    assert route.called
    sent_request = route.calls.last.request
    assert "User-Agent" in sent_request.headers
    assert "firip" in sent_request.headers["User-Agent"].lower()


@pytest.mark.asyncio
async def test_run_marks_failed_not_raised_on_403():
    connector = NwsAlertsConnector()
    with respx.mock:
        respx.get(url__regex=r".*api\.weather\.gov.*").mock(return_value=Response(403, text="Forbidden"))
        result = await connector.run(area="FL")
    assert result.status == "failed"
    assert result.records == []
