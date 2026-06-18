"""Tests for the deterministic risk-scoring engine.

Asserts: weight dicts sum to 1.0, grade thresholds map correctly at
boundaries, and compute_property_risk_score/compute_county_risk_score are
pure (same inputs -> same output) and produce an explanation mentioning
every contributing factor.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.core.registry import get_registry
from app.services.scoring import (
    FactorInput,
    compute_county_risk_score,
    compute_property_risk_score,
    score_to_grade,
)

registry = get_registry()


def test_property_weights_sum_to_one():
    total = sum(registry.property_risk_weights.values())
    assert total == pytest.approx(1.0, abs=1e-6)


def test_county_weights_sum_to_one():
    total = sum(registry.county_risk_weights.values())
    assert total == pytest.approx(1.0, abs=1e-6)


@pytest.mark.parametrize(
    "score,expected_grade",
    [
        (0, "A"),
        (19.99, "A"),
        (20, "B"),  # max is exclusive: score == max belongs to the next bucket
        (39.99, "B"),
        (40, "C"),
        (59.99, "C"),
        (60, "D"),
        (79.99, "D"),
        (80, "F"),
        (100, "F"),
    ],
)
def test_grade_thresholds_at_boundaries(score, expected_grade):
    assert score_to_grade(score) == expected_grade


def _full_property_inputs(normalized: float) -> dict[str, FactorInput]:
    return {
        key: FactorInput(raw_value=normalized, normalized_score=normalized, source_id="fema-nfhl")
        for key in registry.property_risk_weights
    }


def _full_county_inputs(normalized: float) -> dict[str, FactorInput]:
    return {
        key: FactorInput(raw_value=normalized, normalized_score=normalized, source_id="nws-alerts")
        for key in registry.county_risk_weights
    }


def test_property_score_all_zero_is_grade_a():
    result = compute_property_risk_score(_full_property_inputs(0.0))
    assert result.score == 0.0
    assert result.grade == "A"


def test_property_score_all_max_is_grade_f():
    result = compute_property_risk_score(_full_property_inputs(100.0))
    assert result.score == 100.0
    assert result.grade == "F"


def test_property_score_is_pure():
    now = datetime(2026, 6, 18, tzinfo=UTC)
    inputs = _full_property_inputs(55.0)
    r1 = compute_property_risk_score(inputs, now=now)
    r2 = compute_property_risk_score(inputs, now=now)
    assert r1.score == r2.score
    assert r1.grade == r2.grade
    assert r1.explanation == r2.explanation
    assert r1.model_version == r2.model_version == registry.model_version


def test_county_score_is_pure():
    now = datetime(2026, 6, 18, tzinfo=UTC)
    inputs = _full_county_inputs(33.0)
    r1 = compute_county_risk_score(inputs, now=now)
    r2 = compute_county_risk_score(inputs, now=now)
    assert r1.score == r2.score
    assert r1.explanation == r2.explanation


def test_property_explanation_mentions_every_factor():
    result = compute_property_risk_score(_full_property_inputs(42.0))
    for key in registry.property_risk_weights:
        # Every factor's label must appear in the explanation text.
        matching = [f for f in result.factors if f.key == key]
        assert len(matching) == 1
        assert matching[0].label in result.explanation


def test_county_explanation_mentions_every_factor():
    result = compute_county_risk_score(_full_county_inputs(42.0))
    for key in registry.county_risk_weights:
        matching = [f for f in result.factors if f.key == key]
        assert len(matching) == 1
        assert matching[0].label in result.explanation


def test_missing_factor_defaults_to_zero_not_error():
    # Only supply one of six property factors; others should default to 0
    # normalized score rather than raising.
    inputs = {"fema_flood_zone": FactorInput(raw_value="AE", normalized_score=80.0, source_id="fema-nfhl")}
    result = compute_property_risk_score(inputs)
    expected = 80.0 * registry.property_risk_weights["fema_flood_zone"]
    assert result.score == pytest.approx(expected, abs=1e-6)
    assert "unavailable" in result.explanation


def test_weighted_score_matches_manual_calculation():
    inputs = {
        key: FactorInput(raw_value=None, normalized_score=float(i * 10))
        for i, key in enumerate(registry.property_risk_weights, start=1)
    }
    result = compute_property_risk_score(inputs)
    expected = sum(
        float(i * 10) * w
        for i, w in enumerate(registry.property_risk_weights.values(), start=1)
    )
    assert result.score == pytest.approx(round(expected, 2), abs=1e-6)
