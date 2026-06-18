import scoringData from "../../data/scoring.json";

/**
 * Canonical risk-scoring weights, loaded from packages/shared/data/scoring.json.
 * That JSON file is the single source of truth shared with the Python scoring
 * engine in apps/api - edit it there, not here, so the web explanation panel
 * never drifts from the persisted backend score.
 */
export const PROPERTY_RISK_WEIGHTS = scoringData.property_risk_weights;
export const COUNTY_RISK_WEIGHTS = scoringData.county_risk_weights;
export const SCORING_MODEL_VERSION = scoringData.model_version;

export type PropertyRiskFactorKey = keyof typeof PROPERTY_RISK_WEIGHTS;
export type CountyRiskFactorKey = keyof typeof COUNTY_RISK_WEIGHTS;

export type RiskGrade = "A" | "B" | "C" | "D" | "F";

/** 0-100 score -> A-F letter grade. Upper bound is exclusive; null = unbounded. */
export const RISK_GRADE_THRESHOLDS: { max: number; grade: RiskGrade }[] = scoringData.grade_thresholds.map(
  (t) => ({ max: t.max ?? Infinity, grade: t.grade as RiskGrade })
);

export function scoreToGrade(score: number): RiskGrade {
  const clamped = Math.max(0, Math.min(100, score));
  for (const { max, grade } of RISK_GRADE_THRESHOLDS) {
    if (clamped < max) return grade;
  }
  return "F";
}
