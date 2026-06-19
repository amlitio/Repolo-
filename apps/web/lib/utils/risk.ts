import type { RiskGrade } from "@firip/shared";

/**
 * Color coding for risk grades, derived once here from the shared RiskGrade
 * union so every component (map legend, dashboards, intelligence panel)
 * stays visually consistent. Do not invent a parallel scale - if a new grade
 * is ever added to @firip/shared this will fail to type-check, which is the
 * point.
 */
const GRADE_COLORS: Record<RiskGrade, string> = {
  A: "#22c55e", // green-500
  B: "#84cc16", // lime-500
  C: "#eab308", // yellow-500
  D: "#f97316", // orange-500
  F: "#ef4444", // red-500
};

const GRADE_TEXT_CLASSES: Record<RiskGrade, string> = {
  A: "text-emerald-400",
  B: "text-lime-400",
  C: "text-yellow-400",
  D: "text-orange-400",
  F: "text-red-400",
};

const GRADE_BADGE_CLASSES: Record<RiskGrade, string> = {
  A: "bg-emerald-500/15 text-emerald-400 border-emerald-500/40",
  B: "bg-lime-500/15 text-lime-400 border-lime-500/40",
  C: "bg-yellow-500/15 text-yellow-400 border-yellow-500/40",
  D: "bg-orange-500/15 text-orange-400 border-orange-500/40",
  F: "bg-red-500/15 text-red-400 border-red-500/40",
};

export function gradeColor(grade: RiskGrade): string {
  return GRADE_COLORS[grade];
}

export function gradeTextClass(grade: RiskGrade): string {
  return GRADE_TEXT_CLASSES[grade];
}

export function gradeBadgeClass(grade: RiskGrade): string {
  return GRADE_BADGE_CLASSES[grade];
}
