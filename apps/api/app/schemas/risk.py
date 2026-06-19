"""Risk scoring schemas, mirroring packages/shared/src/types/api.ts
(RiskFactor, PropertyRiskScore, CountyRiskScore)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

RiskGrade = str  # "A" | "B" | "C" | "D" | "F"


class RiskFactor(BaseModel):
    key: str
    label: str
    weight: float
    raw_value: float | str | None
    normalized_score: float
    source_id: str | None


class PropertyRiskScore(BaseModel):
    property_id: str
    score: float
    grade: RiskGrade
    factors: list[RiskFactor]
    explanation: str
    model_version: str
    computed_at: datetime


class CountyRiskScore(BaseModel):
    county_fips: str
    county_name: str
    score: float
    grade: RiskGrade
    factors: list[RiskFactor]
    explanation: str
    model_version: str
    computed_at: datetime


class RiskExplainResponse(BaseModel):
    property_id: str | None = None
    county_fips: str | None = None
    factors: list[RiskFactor]
    methodology: str = Field(..., description="Longer-form explanation of the scoring methodology.")
    model_version: str
    generated_at: datetime
