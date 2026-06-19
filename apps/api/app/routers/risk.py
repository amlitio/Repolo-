"""Risk scoring endpoints.

Scores are computed by apps/workers' risk_modeling_agent and persisted to
property_risk_scores / county_risk_scores / score_explanations. These routes
only READ the persisted scores - they never compute-on-the-fly and never
fabricate a score for an unknown property/county; an unscored or unknown
subject yields a 404 through the standard error envelope.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.core.registry import get_registry
from app.db import get_db
from app.models.risk import CountyRiskScore as CountyRiskScoreModel
from app.models.risk import Property
from app.models.risk import PropertyRiskScore as PropertyRiskScoreModel
from app.models.risk import ScoreExplanation
from app.models.types import is_valid_guid
from app.schemas.risk import CountyRiskScore, PropertyRiskScore, RiskExplainResponse, RiskFactor

router = APIRouter(tags=["risk"])


def _factors_from_json(raw: str) -> list[RiskFactor]:
    return [RiskFactor(**f) for f in json.loads(raw)]


@router.get(
    "/risk/property",
    response_model=PropertyRiskScore,
    summary="Get a property's risk score",
    description="Looks up the most recently persisted PropertyRiskScore for a property, by address or "
    "property_id. 404 (standard error envelope) if the property is unknown or has not been scored yet - "
    "scores are never fabricated on the fly.",
)
async def get_property_risk(
    db: AsyncSession = Depends(get_db),
    address: str | None = Query(None),
    property_id: str | None = Query(None),
) -> PropertyRiskScore:
    if not address and not property_id:
        raise NotFoundError("Provide either 'address' or 'property_id'")

    resolved_property_id = property_id
    if not resolved_property_id and address:
        result = await db.execute(select(Property).where(Property.address == address))
        prop = result.scalar_one_or_none()
        if prop is None:
            raise NotFoundError(f"No property found for address '{address}'")
        resolved_property_id = prop.id

    if not is_valid_guid(resolved_property_id):
        # A malformed/unknown id can never have a persisted score - 404
        # cleanly rather than letting the GUID column raise on bind.
        raise NotFoundError(f"No risk score has been computed for property '{resolved_property_id}'")

    result = await db.execute(
        select(PropertyRiskScoreModel)
        .where(PropertyRiskScoreModel.property_id == resolved_property_id)
        .order_by(PropertyRiskScoreModel.computed_at.desc())
    )
    score = result.scalars().first()
    if score is None:
        raise NotFoundError(f"No risk score has been computed for property '{resolved_property_id}'")

    return PropertyRiskScore(
        property_id=score.property_id,
        score=score.score,
        grade=score.grade,
        factors=_factors_from_json(score.factors_json),
        explanation=score.explanation,
        model_version=score.model_version,
        computed_at=score.computed_at,
    )


@router.get(
    "/risk/county",
    response_model=CountyRiskScore,
    summary="Get a county's risk score",
    description="Looks up the most recently persisted CountyRiskScore. 404 if the county FIPS is unknown "
    "or has not been scored yet.",
)
async def get_county_risk(
    db: AsyncSession = Depends(get_db),
    fips: str = Query(...),
) -> CountyRiskScore:
    registry = get_registry()
    if registry.get_county_by_fips(fips) is None:
        raise NotFoundError(f"Unknown county FIPS '{fips}'")

    result = await db.execute(
        select(CountyRiskScoreModel)
        .where(CountyRiskScoreModel.county_fips == fips)
        .order_by(CountyRiskScoreModel.computed_at.desc())
    )
    score = result.scalars().first()
    if score is None:
        raise NotFoundError(f"No risk score has been computed for county '{fips}'")

    return CountyRiskScore(
        county_fips=score.county_fips,
        county_name=score.county_name,
        score=score.score,
        grade=score.grade,
        factors=_factors_from_json(score.factors_json),
        explanation=score.explanation,
        model_version=score.model_version,
        computed_at=score.computed_at,
    )


@router.get(
    "/risk/explain",
    response_model=RiskExplainResponse,
    summary="Get the persisted methodology explanation for a score",
    description="Returns the persisted factors plus a longer methodology narrative for a property or "
    "county. 404 if neither identifier resolves to a persisted explanation.",
)
async def explain_risk(
    db: AsyncSession = Depends(get_db),
    property_id: str | None = Query(None),
    county_fips: str | None = Query(None),
) -> RiskExplainResponse:
    if not property_id and not county_fips:
        raise NotFoundError("Provide either 'property_id' or 'county_fips'")

    if property_id and not is_valid_guid(property_id):
        # A malformed/unknown id can never have a persisted explanation -
        # 404 cleanly rather than letting the GUID column raise on bind.
        raise NotFoundError("No persisted explanation found for the given identifier")

    stmt = select(ScoreExplanation)
    if property_id:
        stmt = stmt.where(ScoreExplanation.property_id == property_id)
    else:
        stmt = stmt.where(ScoreExplanation.county_fips == county_fips)
    stmt = stmt.order_by(ScoreExplanation.generated_at.desc())

    result = await db.execute(stmt)
    explanation = result.scalars().first()
    if explanation is None:
        raise NotFoundError("No persisted explanation found for the given identifier")

    return RiskExplainResponse(
        property_id=explanation.property_id,
        county_fips=explanation.county_fips,
        factors=_factors_from_json(explanation.factors_json),
        methodology=explanation.methodology,
        model_version=explanation.model_version,
        generated_at=explanation.generated_at,
    )
