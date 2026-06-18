import { describe, expect, it } from "vitest";
import { RISK_GRADE_THRESHOLDS, type RiskGrade } from "@firip/shared";
import { gradeBadgeClass, gradeColor, gradeTextClass } from "@/lib/utils/risk";

describe("risk grade color mapping", () => {
  it("defines a color, text class, and badge class for every grade in the shared RiskGrade union", () => {
    const grades = RISK_GRADE_THRESHOLDS.map((t) => t.grade);
    for (const grade of grades) {
      expect(gradeColor(grade)).toMatch(/^#[0-9a-f]{6}$/i);
      expect(gradeTextClass(grade)).toContain("text-");
      expect(gradeBadgeClass(grade)).toContain("border-");
    }
  });

  it("orders colors from green (A) toward red (F) without inventing a separate scale", () => {
    const order: RiskGrade[] = ["A", "B", "C", "D", "F"];
    const colors = order.map(gradeColor);
    // Sanity check: A is green-ish, F is red-ish - first byte of hex is low for green-dominant, high for red-dominant.
    expect(colors[0]?.toLowerCase()).toBe("#22c55e");
    expect(colors[colors.length - 1]?.toLowerCase()).toBe("#ef4444");
  });
});
