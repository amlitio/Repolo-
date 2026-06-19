"""Risk Modeling agent.

docs/architecture.md names exactly four scheduled agents (Data Discovery,
Water Intelligence, Risk Modeling, Research) and doesn't give FEMA/NOAA
ingestion its own agent. Since `compute_county_risk_score` /
`compute_property_risk_score` (app/services/scoring.py) need fresh
`flood_zones`, `fema_disasters`, `mitigation_projects`, `weather_alerts`,
and `hurricane_tracks` rows to score against, this agent owns both halves:
it runs the FEMA NFHL/OpenFEMA, NWS Alerts, and NHC connectors first, then
recomputes every county's (and any persisted property's) risk score from
whatever is now in the database - never inventing a factor value for a
source that hasn't produced data yet.

Two honesty rules drive the per-county factor computation below:
- `flood_zones` has no natural external id to upsert against, so a
  successful NFHL fetch fully replaces the table (a failed/degraded fetch
  leaves prior rows untouched - see `_refresh_flood_zones`).
- A factor key is included for a county only when we have a real signal
  for it. "Zero" is only ever recorded once ingestion has produced at
  least one row somewhere (e.g. "zero active alerts right now" is a real
  signal once NWS ingestion has run at all); if a table is still
  completely empty, the factor key is omitted entirely rather than
  defaulting to a misleading zero - compute_*_risk_score already treats a
  missing key as normalized_score=0 and labels it "raw value unavailable"
  in the explanation, which is the honest outcome we want.

Properties have no parcel-level flood-zone geometry intersection in this
MVP: app/models/types.py documents that real point-in-polygon queries are
reserved for `@pytest.mark.integration` tests against Postgres+PostGIS,
and that constraint applies equally here. Each property's factors are
therefore taken from its county's already-computed factor inputs as a
documented coarse-grained proxy - a real, computed signal, just not
parcel-specific - never a fabricated value.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from app.connectors.fema_nfhl import FemaNfhlConnector
from app.connectors.fema_openfema import (
    DisasterDeclarationRecord,
    FemaOpenFemaDisasterDeclarationsConnector,
    FemaOpenFemaHazardMitigationConnector,
    HazardMitigationProjectRecord,
)
from app.connectors.nhc import HurricaneTrackRecord, NhcConnector
from app.connectors.nws_alerts import NwsAlertsConnector, WeatherAlertRecord
from app.core.registry import Registry, get_registry
from app.models.flood import FemaDisaster, FloodZone, MitigationProject
from app.models.mixins import new_uuid
from app.models.risk import CountyRiskScore, Property, PropertyRiskScore, ScoreExplanation
from app.models.weather import HurricaneTrack, WeatherAlert
from app.services.scoring import (
    FactorInput,
    RiskFactorResult,
    compute_county_risk_score,
    compute_property_risk_score,
)
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from worker.agents.base import Agent, AgentRunResult
from worker.persistence import record_connector_run

_SEVERITY_SCORES = {"extreme": 100.0, "severe": 75.0, "moderate": 50.0, "minor": 25.0}

# Maps each property-level factor (app/services/scoring.py's
# _PROPERTY_FACTOR_LABELS) to the county-level factor it's proxied from.
# water_level_trend and elevation_proximity_to_water have no real data
# source in this MVP and are intentionally absent from this map.
_PROPERTY_FACTOR_FROM_COUNTY = {
    "fema_flood_zone": "flood_zone_coverage",
    "active_weather_alerts": "active_alert_severity",
    "hurricane_exposure": "hurricane_exposure_history",
    "historical_claims_mitigation": "claims_and_mitigation_density",
}


def _factors_to_json(factors: list[RiskFactorResult]) -> str:
    return json.dumps(
        [
            {
                "key": f.key,
                "label": f.label,
                "weight": f.weight,
                "raw_value": f.raw_value,
                "normalized_score": f.normalized_score,
                "source_id": f.source_id,
            }
            for f in factors
        ]
    )


async def _refresh_flood_zones(session: AsyncSession, result: Any) -> tuple[int, int]:
    """Full statewide replace of `flood_zones` on each successful NFHL
    fetch (the model has no natural external id to upsert against). A
    failed/degraded fetch leaves previously-ingested rows untouched.
    Returns (inserted, skipped_missing_fips)."""

    if result.status != "success":
        return 0, 0
    await session.execute(delete(FloodZone))
    inserted = 0
    skipped = 0
    for record in result.records:
        if not record.fips:
            # FloodZone.fips is NOT NULL; CO_FIPS is genuinely absent on
            # some NFHL features (varies by FEMA region) - skip rather than
            # fabricate a county code.
            skipped += 1
            continue
        session.add(
            FloodZone(
                id=new_uuid(),
                fips=record.fips,
                zone_label=record.zone_label,
                is_special_flood_hazard_area=record.is_special_flood_hazard_area,
                base_flood_elevation=record.base_flood_elevation,
                geometry=record.geometry,
                effective_date=record.effective_date,
            )
        )
        inserted += 1
    await session.flush()
    return inserted, skipped


async def _insert_fema_disaster_if_new(session: AsyncSession, record: DisasterDeclarationRecord) -> bool:
    if not record.county_fips:
        return False
    existing = await session.execute(
        select(FemaDisaster).where(
            FemaDisaster.disaster_number == record.disaster_number,
            FemaDisaster.county_fips == record.county_fips,
        )
    )
    if existing.scalar_one_or_none() is not None:
        return False
    session.add(
        FemaDisaster(
            id=new_uuid(),
            disaster_number=record.disaster_number,
            county_fips=record.county_fips,
            state=record.state,
            declaration_type=record.declaration_type,
            incident_type=record.incident_type,
            title=record.title,
            declaration_date=record.declaration_date,
        )
    )
    await session.flush()
    return True


async def _insert_mitigation_project_if_new(
    session: AsyncSession, record: HazardMitigationProjectRecord
) -> bool:
    existing = await session.execute(
        select(MitigationProject).where(MitigationProject.project_id == record.project_id)
    )
    if existing.scalar_one_or_none() is not None:
        return False
    session.add(
        MitigationProject(
            id=new_uuid(),
            project_id=record.project_id,
            county_fips=record.county_fips,
            program=record.program,
            status=record.status,
            title=record.title,
            federal_share_obligated=record.federal_share_obligated,
            approval_date=record.approval_date,
        )
    )
    await session.flush()
    return True


async def _upsert_weather_alert(session: AsyncSession, source_id: str, record: WeatherAlertRecord) -> None:
    existing = await session.execute(
        select(WeatherAlert).where(WeatherAlert.external_id == record.external_id)
    )
    alert = existing.scalar_one_or_none()
    if alert is None:
        alert = WeatherAlert(id=new_uuid(), external_id=record.external_id, source_id=source_id)
        session.add(alert)
    alert.event = record.event
    alert.severity = record.severity
    alert.certainty = record.certainty
    alert.urgency = record.urgency
    alert.headline = record.headline
    alert.description = record.description
    alert.area_desc = record.area_desc
    alert.county_fips_json = json.dumps(record.county_fips)
    alert.effective_at = record.effective_at
    alert.expires_at = record.expires_at
    alert.is_active = True
    await session.flush()


async def _deactivate_stale_alerts(session: AsyncSession, seen_external_ids: set[str]) -> int:
    """NWS's /alerts/active feed only returns currently-active alerts -
    anything we'd previously marked active that's absent from this fetch
    has expired or been canceled upstream."""

    result = await session.execute(select(WeatherAlert).where(WeatherAlert.is_active.is_(True)))
    deactivated = 0
    for alert in result.scalars().all():
        if alert.external_id not in seen_external_ids:
            alert.is_active = False
            deactivated += 1
    if deactivated:
        await session.flush()
    return deactivated


async def _insert_hurricane_track_if_new(session: AsyncSession, record: HurricaneTrackRecord) -> bool:
    existing = await session.execute(
        select(HurricaneTrack).where(
            HurricaneTrack.storm_id == record.storm_id,
            HurricaneTrack.advisory_num == record.advisory_num,
        )
    )
    if existing.scalar_one_or_none() is not None:
        return False
    session.add(
        HurricaneTrack(
            id=new_uuid(),
            storm_id=record.storm_id,
            name=record.name,
            season=record.season,
            advisory_num=record.advisory_num,
            classification=record.classification,
            issued_at=record.issued_at,
            geometry=record.geometry,
        )
    )
    await session.flush()
    return True


async def _flood_zone_coverage_by_fips(session: AsyncSession) -> dict[str, FactorInput]:
    result = await session.execute(select(FloodZone.fips, FloodZone.is_special_flood_hazard_area))
    totals: dict[str, int] = {}
    sfha: dict[str, int] = {}
    for fips, is_sfha in result.all():
        totals[fips] = totals.get(fips, 0) + 1
        if is_sfha:
            sfha[fips] = sfha.get(fips, 0) + 1
    return {
        fips: FactorInput(
            raw_value=round(100.0 * sfha.get(fips, 0) / total, 1),
            normalized_score=round(100.0 * sfha.get(fips, 0) / total, 1),
            source_id="fema-nfhl",
        )
        for fips, total in totals.items()
        if total > 0
    }


async def _active_alert_severity_by_fips(
    session: AsyncSession, registry: Registry
) -> dict[str, FactorInput] | None:
    any_row = await session.execute(select(WeatherAlert.id).limit(1))
    if any_row.scalar_one_or_none() is None:
        return None

    active = await session.execute(select(WeatherAlert).where(WeatherAlert.is_active.is_(True)))
    best_by_fips: dict[str, float] = {}
    for alert in active.scalars().all():
        score = _SEVERITY_SCORES.get(alert.severity.strip().lower(), 0.0)
        for fips in json.loads(alert.county_fips_json):
            best_by_fips[fips] = max(best_by_fips.get(fips, 0.0), score)

    return {
        county["fips"]: FactorInput(
            raw_value=best_by_fips.get(county["fips"], 0.0),
            normalized_score=best_by_fips.get(county["fips"], 0.0),
            source_id="nws-alerts",
        )
        for county in registry.counties
    }


async def _hurricane_exposure_by_fips(
    session: AsyncSession, registry: Registry
) -> dict[str, FactorInput] | None:
    any_row = await session.execute(select(FemaDisaster.id).limit(1))
    if any_row.scalar_one_or_none() is None:
        return None

    result = await session.execute(select(FemaDisaster.county_fips, FemaDisaster.incident_type))
    counts: dict[str, int] = {}
    for fips, incident_type in result.all():
        if fips and "hurricane" in (incident_type or "").lower():
            counts[fips] = counts.get(fips, 0) + 1

    return {
        county["fips"]: FactorInput(
            raw_value=counts.get(county["fips"], 0),
            normalized_score=min(100.0, counts.get(county["fips"], 0) * 20.0),
            source_id="fema-openfema-disaster-declarations",
        )
        for county in registry.counties
    }


async def _mitigation_density_by_fips(
    session: AsyncSession, registry: Registry
) -> dict[str, FactorInput] | None:
    any_row = await session.execute(select(MitigationProject.id).limit(1))
    if any_row.scalar_one_or_none() is None:
        return None

    result = await session.execute(select(MitigationProject.county_fips))
    counts: dict[str, int] = {}
    for (fips,) in result.all():
        if fips:
            counts[fips] = counts.get(fips, 0) + 1

    return {
        county["fips"]: FactorInput(
            raw_value=counts.get(county["fips"], 0),
            normalized_score=min(100.0, counts.get(county["fips"], 0) * 10.0),
            source_id="fema-openfema-hazard-mitigation",
        )
        for county in registry.counties
    }


async def _score_counties(
    session: AsyncSession,
    registry: Registry,
    flood_by_fips: dict[str, FactorInput],
    alert_by_fips: dict[str, FactorInput] | None,
    hurricane_by_fips: dict[str, FactorInput] | None,
    mitigation_by_fips: dict[str, FactorInput] | None,
) -> tuple[int, dict[str, dict[str, FactorInput]]]:
    now = datetime.now(UTC)
    factor_inputs_by_fips: dict[str, dict[str, FactorInput]] = {}
    scored = 0
    for county in registry.counties:
        fips = county["fips"]
        factor_inputs: dict[str, FactorInput] = {}
        if fips in flood_by_fips:
            factor_inputs["flood_zone_coverage"] = flood_by_fips[fips]
        if alert_by_fips is not None:
            factor_inputs["active_alert_severity"] = alert_by_fips[fips]
        if hurricane_by_fips is not None:
            factor_inputs["hurricane_exposure_history"] = hurricane_by_fips[fips]
        if mitigation_by_fips is not None:
            factor_inputs["claims_and_mitigation_density"] = mitigation_by_fips[fips]
        # water_level_trend and drought_flood_indicators have no real data
        # source in this MVP and are intentionally left out of
        # factor_inputs.
        factor_inputs_by_fips[fips] = factor_inputs

        result = compute_county_risk_score(factor_inputs, registry=registry, now=now)
        session.add(
            CountyRiskScore(
                id=new_uuid(),
                county_fips=fips,
                county_name=county["name"],
                score=result.score,
                grade=result.grade,
                factors_json=_factors_to_json(result.factors),
                explanation=result.explanation,
                model_version=result.model_version,
                computed_at=result.computed_at,
            )
        )
        session.add(
            ScoreExplanation(
                id=new_uuid(),
                county_fips=fips,
                model_version=result.model_version,
                methodology=result.explanation,
                factors_json=_factors_to_json(result.factors),
                generated_at=result.computed_at,
            )
        )
        scored += 1
    await session.flush()
    return scored, factor_inputs_by_fips


async def _score_properties(
    session: AsyncSession, registry: Registry, county_factor_inputs_by_fips: dict[str, dict[str, FactorInput]]
) -> int:
    result = await session.execute(select(Property))
    properties = result.scalars().all()
    now = datetime.now(UTC)
    scored = 0
    for prop in properties:
        county_factors = county_factor_inputs_by_fips.get(prop.county_fips or "", {})
        factor_inputs: dict[str, FactorInput] = {
            property_key: county_factors[county_key]
            for property_key, county_key in _PROPERTY_FACTOR_FROM_COUNTY.items()
            if county_key in county_factors
        }
        result_score = compute_property_risk_score(factor_inputs, registry=registry, now=now)
        session.add(
            PropertyRiskScore(
                id=new_uuid(),
                property_id=prop.id,
                score=result_score.score,
                grade=result_score.grade,
                factors_json=_factors_to_json(result_score.factors),
                explanation=result_score.explanation,
                model_version=result_score.model_version,
                computed_at=result_score.computed_at,
            )
        )
        session.add(
            ScoreExplanation(
                id=new_uuid(),
                property_id=prop.id,
                model_version=result_score.model_version,
                methodology=result_score.explanation,
                factors_json=_factors_to_json(result_score.factors),
                generated_at=result_score.computed_at,
            )
        )
        scored += 1
    if scored:
        await session.flush()
    return scored


class RiskModelingAgent(Agent):
    name = "risk_modeling"

    async def execute(self, session: AsyncSession) -> AgentRunResult:
        started_at = datetime.now(UTC)
        registry = get_registry()
        details: dict[str, Any] = {}

        nfhl_result = await FemaNfhlConnector().run()
        await record_connector_run(session, nfhl_result)
        flood_zones_inserted, flood_zones_skipped = await _refresh_flood_zones(session, nfhl_result)
        details["fema_nfhl"] = {
            "status": nfhl_result.status,
            "flood_zones_inserted": flood_zones_inserted,
            "skipped_missing_fips": flood_zones_skipped,
        }

        disasters_result = await FemaOpenFemaDisasterDeclarationsConnector().run()
        await record_connector_run(session, disasters_result)
        disasters_inserted = 0
        if disasters_result.status == "success":
            for record in disasters_result.records:
                disasters_inserted += int(await _insert_fema_disaster_if_new(session, record))
        details["fema_disaster_declarations"] = {
            "status": disasters_result.status,
            "inserted": disasters_inserted,
        }

        mitigation_result = await FemaOpenFemaHazardMitigationConnector().run()
        await record_connector_run(session, mitigation_result)
        mitigation_inserted = 0
        if mitigation_result.status == "success":
            for record in mitigation_result.records:
                mitigation_inserted += int(await _insert_mitigation_project_if_new(session, record))
        details["fema_hazard_mitigation"] = {
            "status": mitigation_result.status,
            "inserted": mitigation_inserted,
        }

        alerts_result = await NwsAlertsConnector().run()
        await record_connector_run(session, alerts_result)
        alerts_upserted = 0
        deactivated = 0
        if alerts_result.status == "success":
            seen_ids: set[str] = set()
            for record in alerts_result.records:
                await _upsert_weather_alert(session, alerts_result.source_id, record)
                seen_ids.add(record.external_id)
                alerts_upserted += 1
            deactivated = await _deactivate_stale_alerts(session, seen_ids)
        details["nws_alerts"] = {
            "status": alerts_result.status,
            "upserted": alerts_upserted,
            "deactivated": deactivated,
        }

        hurricanes_result = await NhcConnector().run()
        await record_connector_run(session, hurricanes_result)
        hurricanes_inserted = 0
        if hurricanes_result.status == "success":
            for record in hurricanes_result.records:
                hurricanes_inserted += int(await _insert_hurricane_track_if_new(session, record))
        details["nhc_current_storms"] = {"status": hurricanes_result.status, "inserted": hurricanes_inserted}

        flood_by_fips = await _flood_zone_coverage_by_fips(session)
        alert_by_fips = await _active_alert_severity_by_fips(session, registry)
        hurricane_by_fips = await _hurricane_exposure_by_fips(session, registry)
        mitigation_by_fips = await _mitigation_density_by_fips(session, registry)

        counties_scored, county_factor_inputs_by_fips = await _score_counties(
            session, registry, flood_by_fips, alert_by_fips, hurricane_by_fips, mitigation_by_fips
        )
        details["counties_scored"] = counties_scored

        properties_scored = await _score_properties(session, registry, county_factor_inputs_by_fips)
        details["properties_scored"] = properties_scored

        finished_at = datetime.now(UTC)
        ingestion_statuses = [
            nfhl_result.status,
            disasters_result.status,
            mitigation_result.status,
            alerts_result.status,
            hurricanes_result.status,
        ]
        overall_status = "success" if all(s == "success" for s in ingestion_statuses) else "partial"
        return AgentRunResult(
            agent_name=self.name,
            status=overall_status,
            started_at=started_at,
            finished_at=finished_at,
            summary=(
                f"Scored {counties_scored} county(ies) and {properties_scored} property(ies) under "
                f"model {registry.model_version}."
            ),
            details=details,
        )
