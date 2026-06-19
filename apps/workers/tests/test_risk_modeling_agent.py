"""Tests for RiskModelingAgent: ingestion persistence (dedupe/upsert/full-replace
strategies per table) and the honest-factor-omission scoring behavior,
isolated from connector network/parsing concerns by monkeypatching each
Connector subclass's `run()` with a canned ConnectorRunResult.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime

import pytest
from app.connectors.base import ConnectorRunResult
from app.connectors.fema_nfhl import FemaNfhlConnector, NfhlFloodZoneRecord
from app.connectors.fema_openfema import (
    DisasterDeclarationRecord,
    FemaOpenFemaDisasterDeclarationsConnector,
    FemaOpenFemaHazardMitigationConnector,
    HazardMitigationProjectRecord,
)
from app.connectors.nhc import HurricaneTrackRecord, NhcConnector
from app.connectors.nws_alerts import NwsAlertsConnector, WeatherAlertRecord
from app.core.registry import get_registry
from app.models.flood import FemaDisaster, FloodZone, MitigationProject
from app.models.risk import CountyRiskScore, Property, PropertyRiskScore
from app.models.weather import HurricaneTrack, WeatherAlert
from sqlalchemy import select

from worker.agents.risk_modeling_agent import RiskModelingAgent

NOW = datetime.now(UTC)
MIAMI_DADE_FIPS = "12086"


def _fake_run_factory(records, status="success"):
    async def _fake_run(self, **kwargs):
        return ConnectorRunResult(
            source_id=self.source_id, status=status, started_at=NOW, finished_at=NOW, records=records
        )

    return _fake_run


def _flood_zone_records() -> list[NfhlFloodZoneRecord]:
    return [
        NfhlFloodZoneRecord(
            external_id="1",
            fips=MIAMI_DADE_FIPS,
            zone_label="AE",
            is_special_flood_hazard_area=True,
            base_flood_elevation=8.0,
            geometry={},
            effective_date=None,
        ),
        NfhlFloodZoneRecord(
            external_id="2",
            fips=MIAMI_DADE_FIPS,
            zone_label="X",
            is_special_flood_hazard_area=False,
            base_flood_elevation=None,
            geometry={},
            effective_date=None,
        ),
        NfhlFloodZoneRecord(
            external_id="3",
            fips=None,
            zone_label="AE",
            is_special_flood_hazard_area=True,
            base_flood_elevation=None,
            geometry={},
            effective_date=None,
        ),
    ]


def _disaster_records() -> list[DisasterDeclarationRecord]:
    return [
        DisasterDeclarationRecord(
            external_id="d1",
            disaster_number="4750",
            county_fips=MIAMI_DADE_FIPS,
            state="FL",
            declaration_type="DR",
            incident_type="Hurricane",
            title="Hurricane Test",
            declaration_date=date(2025, 9, 1),
        ),
        DisasterDeclarationRecord(
            external_id="d2",
            disaster_number="4751",
            county_fips=MIAMI_DADE_FIPS,
            state="FL",
            declaration_type="DR",
            incident_type="Severe Storm",
            title="Storm Test",
            declaration_date=date(2025, 9, 2),
        ),
    ]


def _mitigation_records() -> list[HazardMitigationProjectRecord]:
    return [
        HazardMitigationProjectRecord(
            external_id="m1",
            project_id="PROJ-1",
            county_fips=MIAMI_DADE_FIPS,
            program="BRIC",
            status="approved",
            title="Seawall",
            federal_share_obligated=2_500_000.0,
            approval_date=date(2025, 1, 1),
        )
    ]


def _alert_records() -> list[WeatherAlertRecord]:
    return [
        WeatherAlertRecord(
            external_id="alert-1",
            event="Flood Warning",
            severity="Severe",
            certainty="Observed",
            urgency="Immediate",
            headline="Flood Warning",
            description="...",
            area_desc="Miami-Dade",
            county_fips=[MIAMI_DADE_FIPS],
            effective_at=NOW,
            expires_at=NOW,
        )
    ]


def _hurricane_records() -> list[HurricaneTrackRecord]:
    return [
        HurricaneTrackRecord(
            storm_id="AL01",
            name="Test Storm",
            season=2025,
            advisory_num="1",
            classification="Hurricane",
            issued_at=NOW,
            geometry={"type": "Point", "coordinates": [-80.2, 25.8]},
        )
    ]


def _patch_all_ingestion(
    monkeypatch, *, flood=None, disasters=None, mitigation=None, alerts=None, hurricanes=None
):
    monkeypatch.setattr(FemaNfhlConnector, "run", _fake_run_factory(flood or []))
    monkeypatch.setattr(
        FemaOpenFemaDisasterDeclarationsConnector, "run", _fake_run_factory(disasters or [])
    )
    monkeypatch.setattr(
        FemaOpenFemaHazardMitigationConnector, "run", _fake_run_factory(mitigation or [])
    )
    monkeypatch.setattr(NwsAlertsConnector, "run", _fake_run_factory(alerts or []))
    monkeypatch.setattr(NhcConnector, "run", _fake_run_factory(hurricanes or []))


@pytest.mark.asyncio
async def test_full_ingestion_scores_every_county_and_persists_all_tables(db_session, monkeypatch):
    _patch_all_ingestion(
        monkeypatch,
        flood=_flood_zone_records(),
        disasters=_disaster_records(),
        mitigation=_mitigation_records(),
        alerts=_alert_records(),
        hurricanes=_hurricane_records(),
    )

    result = await RiskModelingAgent().run(db_session)

    assert result.status == "success"
    registry = get_registry()
    assert result.details["counties_scored"] == len(registry.counties)

    flood_zones = (await db_session.execute(select(FloodZone))).scalars().all()
    assert len(flood_zones) == 2  # the fips=None record is skipped, not fabricated
    disasters = (await db_session.execute(select(FemaDisaster))).scalars().all()
    assert len(disasters) == 2
    mitigation = (await db_session.execute(select(MitigationProject))).scalars().all()
    assert len(mitigation) == 1
    alerts = (await db_session.execute(select(WeatherAlert))).scalars().all()
    assert len(alerts) == 1
    assert alerts[0].is_active is True
    tracks = (await db_session.execute(select(HurricaneTrack))).scalars().all()
    assert len(tracks) == 1

    miami_score = (
        await db_session.execute(
            select(CountyRiskScore).where(CountyRiskScore.county_fips == MIAMI_DADE_FIPS)
        )
    ).scalar_one()
    factors = {f["key"]: f for f in json.loads(miami_score.factors_json)}
    assert factors["flood_zone_coverage"]["raw_value"] == 50.0  # 1 of 2 zones is SFHA
    assert factors["active_alert_severity"]["normalized_score"] == 75.0  # Severe
    assert factors["hurricane_exposure_history"]["raw_value"] == 1  # only the Hurricane-typed disaster counts
    assert factors["claims_and_mitigation_density"]["raw_value"] == 1

    other_fips = next(c["fips"] for c in registry.counties if c["fips"] != MIAMI_DADE_FIPS)
    other_score = (
        await db_session.execute(select(CountyRiskScore).where(CountyRiskScore.county_fips == other_fips))
    ).scalar_one()
    other_factors = {f["key"]: f for f in json.loads(other_score.factors_json)}
    # No flood_zones row exists for this county at all - omitted (raw_value None), not a fabricated 0.
    assert other_factors["flood_zone_coverage"]["raw_value"] is None
    assert other_factors["flood_zone_coverage"]["normalized_score"] == 0.0
    # NWS/FEMA tables have rows somewhere, so "no alert/disaster here" is an honest, explicit 0.
    assert other_factors["active_alert_severity"]["raw_value"] == 0.0
    assert other_factors["hurricane_exposure_history"]["raw_value"] == 0


@pytest.mark.asyncio
async def test_factors_omitted_entirely_when_tables_are_empty(db_session, monkeypatch):
    _patch_all_ingestion(monkeypatch)  # every connector returns zero records

    result = await RiskModelingAgent().run(db_session)

    assert result.status == "success"
    registry = get_registry()
    target_fips = registry.counties[0]["fips"]
    any_score = (
        await db_session.execute(select(CountyRiskScore).where(CountyRiskScore.county_fips == target_fips))
    ).scalar_one()
    factors = {f["key"]: f for f in json.loads(any_score.factors_json)}
    for key in (
        "flood_zone_coverage",
        "active_alert_severity",
        "hurricane_exposure_history",
        "claims_and_mitigation_density",
    ):
        assert factors[key]["raw_value"] is None
        assert factors[key]["normalized_score"] == 0.0


@pytest.mark.asyncio
async def test_rerunning_does_not_duplicate_disasters_mitigation_or_tracks(db_session, monkeypatch):
    _patch_all_ingestion(
        monkeypatch,
        disasters=_disaster_records(),
        mitigation=_mitigation_records(),
        hurricanes=_hurricane_records(),
    )

    await RiskModelingAgent().run(db_session)
    await RiskModelingAgent().run(db_session)

    assert len((await db_session.execute(select(FemaDisaster))).scalars().all()) == 2
    assert len((await db_session.execute(select(MitigationProject))).scalars().all()) == 1
    assert len((await db_session.execute(select(HurricaneTrack))).scalars().all()) == 1


@pytest.mark.asyncio
async def test_stale_alert_is_deactivated_when_absent_from_next_fetch(db_session, monkeypatch):
    _patch_all_ingestion(monkeypatch, alerts=_alert_records())
    await RiskModelingAgent().run(db_session)

    _patch_all_ingestion(monkeypatch, alerts=[])  # next fetch returns no alerts at all
    await RiskModelingAgent().run(db_session)

    alert = (await db_session.execute(select(WeatherAlert))).scalar_one()
    assert alert.is_active is False


@pytest.mark.asyncio
async def test_failed_flood_zone_fetch_leaves_prior_rows_untouched(db_session, monkeypatch):
    _patch_all_ingestion(monkeypatch, flood=_flood_zone_records())
    await RiskModelingAgent().run(db_session)
    assert len((await db_session.execute(select(FloodZone))).scalars().all()) == 2

    monkeypatch.setattr(FemaNfhlConnector, "run", _fake_run_factory([], status="failed"))
    result = await RiskModelingAgent().run(db_session)

    assert result.status == "partial"
    assert len((await db_session.execute(select(FloodZone))).scalars().all()) == 2


@pytest.mark.asyncio
async def test_property_score_proxies_its_countys_factors(db_session, monkeypatch):
    db_session.add(Property(address="123 Test St", county_fips=MIAMI_DADE_FIPS))
    await db_session.flush()

    _patch_all_ingestion(
        monkeypatch,
        flood=_flood_zone_records(),
        disasters=_disaster_records(),
        mitigation=_mitigation_records(),
        alerts=_alert_records(),
        hurricanes=_hurricane_records(),
    )

    result = await RiskModelingAgent().run(db_session)

    assert result.details["properties_scored"] == 1
    prop_score = (await db_session.execute(select(PropertyRiskScore))).scalar_one()
    factors = {f["key"]: f for f in json.loads(prop_score.factors_json)}
    assert factors["fema_flood_zone"]["raw_value"] == 50.0
    assert factors["active_weather_alerts"]["normalized_score"] == 75.0
    # No real data source backs these two in this MVP - always omitted, never fabricated.
    assert factors["water_level_trend"]["raw_value"] is None
    assert factors["elevation_proximity_to_water"]["raw_value"] is None
