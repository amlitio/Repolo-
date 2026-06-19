"""Tests for WaterIntelligenceAgent's persistence logic (upsert/dedupe/landing),
isolated from connector network/parsing concerns (already covered by
apps/api's own connector tests) by monkeypatching each Connector subclass's
`run()` with a canned ConnectorRunResult.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.connectors.base import ConnectorRunResult
from app.connectors.usgs_water import (
    UsgsDailyValuesConnector,
    UsgsObservationRecord,
    UsgsStationRecord,
    UsgsWaterStationsConnector,
)
from app.connectors.wmd_arcgis import WmdArcGisConnector, WmdFeatureRecord
from app.models.water import WaterObservation, WaterStation
from sqlalchemy import select

from worker.agents.water_intelligence_agent import WaterIntelligenceAgent

NOW = datetime.now(UTC)


def _station_record(external_id: str = "USGS-1") -> UsgsStationRecord:
    return UsgsStationRecord(
        external_id=external_id,
        name="Test Station",
        county_fips="12086",
        latitude=25.8,
        longitude=-80.2,
        parameter_types=["00060"],
    )


def _observation_record(station_external_id: str = "USGS-1") -> UsgsObservationRecord:
    return UsgsObservationRecord(
        station_external_id=station_external_id,
        parameter="00060",
        value=123.4,
        unit="ft3/s",
        observed_at=NOW,
        qualifier=None,
    )


def _wmd_feature_record(external_id: str = "1") -> WmdFeatureRecord:
    return WmdFeatureRecord(external_id=external_id, layer_name="canals", geometry={}, properties={})


def _fake_run_factory(records, status="success"):
    async def _fake_run(self, **kwargs):
        return ConnectorRunResult(
            source_id=self.source_id,
            status=status,
            started_at=NOW,
            finished_at=NOW,
            records=records,
        )

    return _fake_run


@pytest.mark.asyncio
async def test_upserts_stations_inserts_observations_and_lands_wmd_features(db_session, monkeypatch):
    monkeypatch.setattr(UsgsWaterStationsConnector, "run", _fake_run_factory([_station_record()]))
    monkeypatch.setattr(UsgsDailyValuesConnector, "run", _fake_run_factory([_observation_record()]))
    monkeypatch.setattr(WmdArcGisConnector, "run", _fake_run_factory([_wmd_feature_record()]))

    result = await WaterIntelligenceAgent().run(db_session)

    assert result.status == "success"
    assert result.details["usgs_stations"]["upserted"] == 1
    assert result.details["usgs_daily_values"]["observations_inserted"] == 1
    # 4 WMD ArcGIS connectors (SFWMD/SJRWMD/SWFWMD/NWFWMD) each land 1 feature;
    # SRWMD stays degraded (is_supported() is False, never patched).
    assert sum(v["landed"] for v in result.details["wmd_districts"].values()) == 4

    stations = (await db_session.execute(select(WaterStation))).scalars().all()
    assert len(stations) == 1
    observations = (await db_session.execute(select(WaterObservation))).scalars().all()
    assert len(observations) == 1


@pytest.mark.asyncio
async def test_rerunning_does_not_duplicate_station_or_observation(db_session, monkeypatch):
    monkeypatch.setattr(UsgsWaterStationsConnector, "run", _fake_run_factory([_station_record()]))
    monkeypatch.setattr(UsgsDailyValuesConnector, "run", _fake_run_factory([_observation_record()]))
    monkeypatch.setattr(WmdArcGisConnector, "run", _fake_run_factory([]))

    await WaterIntelligenceAgent().run(db_session)
    await WaterIntelligenceAgent().run(db_session)

    stations = (await db_session.execute(select(WaterStation))).scalars().all()
    assert len(stations) == 1
    observations = (await db_session.execute(select(WaterObservation))).scalars().all()
    assert len(observations) == 1


@pytest.mark.asyncio
async def test_failed_station_fetch_skips_daily_values_and_reports_partial(db_session, monkeypatch):
    monkeypatch.setattr(
        UsgsWaterStationsConnector, "run", _fake_run_factory([], status="failed")
    )
    monkeypatch.setattr(WmdArcGisConnector, "run", _fake_run_factory([]))

    result = await WaterIntelligenceAgent().run(db_session)

    assert result.status == "partial"
    assert result.details["usgs_daily_values"]["observations_inserted"] == 0
