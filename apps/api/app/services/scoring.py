"""Deterministic risk-scoring engine.

Weights and grade thresholds are loaded at runtime from
packages/shared/data/scoring.json via app.core.registry (never hardcoded
here), so the Python backend and the TypeScript frontend
(packages/shared/src/constants/scoring.ts) can never drift apart.

compute_property_risk_score / compute_county_risk_score are pure functions:
same inputs -> same output, no I/O, no randomness, no wall-clock reads except
the caller-supplied `now` (defaults to utcnow but is injectable for tests).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from app.core.registry import Registry, get_registry

# Human-readable labels for each factor key, used in RiskFactor.label.
_PROPERTY_FACTOR_LABELS: dict[str, str] = {
    "fema_flood_zone": "FEMA Flood Zone",
    "elevation_proximity_to_water": "Elevation / Proximity to Water",
    "active_weather_alerts": "Active Weather Alerts",
    "water_level_trend": "Water Level Trend",
    "hurricane_exposure": "Hurricane Exposure",
    "historical_claims_mitigation": "Historical Claims & Mitigation",
}

_COUNTY_FACTOR_LABELS: dict[str, str] = {
    "flood_zone_coverage": "Flood Zone Coverage",
    "active_alert_severity": "Active Alert Severity",
    "water_level_trend": "Water Level Trend",
    "hurricane_exposure_history": "Hurricane Exposure History",
    "drought_flood_indicators": "Drought / Flood Indicators",
    "claims_and_mitigation_density": "Claims & Mitigation Density",
}


@dataclass(frozen=True)
class FactorInput:
    """A single risk factor's raw value and pre-normalized [0, 100] score.

    `normalized_score` must already be on a 0-100 scale (0 = no risk,
    100 = max risk) before being passed in; this module only applies
    weights and aggregates, it does not invent normalization heuristics
    for upstream raw values.
    """

    raw_value: float | str | None
    normalized_score: float
    source_id: str | None = None


@dataclass(frozen=True)
class RiskFactorResult:
    key: str
    label: str
    weight: float
    raw_value: float | str | None
    normalized_score: float
    source_id: str | None


@dataclass(frozen=True)
class RiskScoreResult:
    score: float
    grade: str
    factors: list[RiskFactorResult]
    explanation: str
    model_version: str
    computed_at: datetime


def score_to_grade(score: float, registry: Registry | None = None) -> str:
    """Map a 0-100 score to a letter grade using scoring.json's
    grade_thresholds. Upper bound (`max`) is exclusive, matching
    packages/shared/src/constants/scoring.ts::scoreToGrade. `max: null` means
    unbounded (always matches if reached)."""

    registry = registry or get_registry()
    clamped = max(0.0, min(100.0, score))
    for threshold in registry.grade_thresholds:
        max_value = threshold["max"]
        if max_value is None or clamped < max_value:
            return threshold["grade"]
    return "F"


def _weighted_aggregate(
    inputs: dict[str, FactorInput],
    weights: dict[str, float],
    labels: dict[str, str],
) -> tuple[float, list[RiskFactorResult]]:
    factors: list[RiskFactorResult] = []
    total = 0.0
    for key, weight in weights.items():
        factor_input = inputs.get(key)
        normalized = 0.0 if factor_input is None else factor_input.normalized_score
        normalized = max(0.0, min(100.0, normalized))
        raw_value = None if factor_input is None else factor_input.raw_value
        source_id = None if factor_input is None else factor_input.source_id
        total += normalized * weight
        factors.append(
            RiskFactorResult(
                key=key,
                label=labels.get(key, key),
                weight=weight,
                raw_value=raw_value,
                normalized_score=normalized,
                source_id=source_id,
            )
        )
    return total, factors


def _build_explanation(subject: str, score: float, grade: str, factors: list[RiskFactorResult]) -> str:
    parts = [
        f"{subject} scored {score:.1f}/100 (grade {grade}) under the FIRIP risk model.",
        "Contributing factors:",
    ]
    for factor in factors:
        parts.append(
            f"- {factor.label} (weight {factor.weight:.0%}): "
            f"normalized score {factor.normalized_score:.1f}/100"
            + (f", raw value {factor.raw_value}" if factor.raw_value is not None else ", raw value unavailable")
            + (f", source: {factor.source_id}" if factor.source_id else "")
        )
    return "\n".join(parts)


def compute_property_risk_score(
    factor_inputs: dict[str, FactorInput],
    registry: Registry | None = None,
    now: datetime | None = None,
) -> RiskScoreResult:
    """Pure function: compute a property's risk score from factor inputs.

    `factor_inputs` keys must match property_risk_weights keys in
    scoring.json (fema_flood_zone, elevation_proximity_to_water, etc.).
    Missing keys are treated as normalized_score=0 (no signal) rather than
    raising, so partial data never crashes scoring - but they do still show
    up in the explanation as "raw value unavailable".
    """

    registry = registry or get_registry()
    weights = registry.property_risk_weights
    score, factors = _weighted_aggregate(factor_inputs, weights, _PROPERTY_FACTOR_LABELS)
    grade = score_to_grade(score, registry)
    explanation = _build_explanation("This property", score, grade, factors)
    return RiskScoreResult(
        score=round(score, 2),
        grade=grade,
        factors=factors,
        explanation=explanation,
        model_version=registry.model_version,
        computed_at=now or datetime.now(UTC),
    )


def compute_county_risk_score(
    factor_inputs: dict[str, FactorInput],
    registry: Registry | None = None,
    now: datetime | None = None,
) -> RiskScoreResult:
    """Pure function: compute a county's risk score from factor inputs.

    `factor_inputs` keys must match county_risk_weights keys in scoring.json
    (flood_zone_coverage, active_alert_severity, etc.).
    """

    registry = registry or get_registry()
    weights = registry.county_risk_weights
    score, factors = _weighted_aggregate(factor_inputs, weights, _COUNTY_FACTOR_LABELS)
    grade = score_to_grade(score, registry)
    explanation = _build_explanation("This county", score, grade, factors)
    return RiskScoreResult(
        score=round(score, 2),
        grade=grade,
        factors=factors,
        explanation=explanation,
        model_version=registry.model_version,
        computed_at=now or datetime.now(UTC),
    )
