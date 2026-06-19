import { describe, expect, it } from "vitest";
import { COUNTIES, SOURCES, getCountyByFips, getCountyByName, getCountiesByWmd } from "./index";
import { scoreToGrade } from "../constants/scoring";

describe("county registry", () => {
  it("contains exactly the 67 Florida counties", () => {
    expect(COUNTIES).toHaveLength(67);
  });

  it("has unique FIPS codes", () => {
    const fipsSet = new Set(COUNTIES.map((c) => c.fips));
    expect(fipsSet.size).toBe(67);
  });

  it("resolves a county by FIPS", () => {
    expect(getCountyByFips("12086")?.name).toBe("Miami-Dade");
  });

  it("resolves a county by name", () => {
    expect(getCountyByName("broward")?.fips).toBe("12011");
  });

  it("groups counties by water management district", () => {
    const sfwmd = getCountiesByWmd("SFWMD");
    expect(sfwmd.length).toBeGreaterThan(10);
    expect(sfwmd.some((c) => c.name === "Miami-Dade")).toBe(true);
  });
});

describe("source registry", () => {
  it("has unique source ids", () => {
    const ids = new Set(SOURCES.map((s) => s.id));
    expect(ids.size).toBe(SOURCES.length);
  });

  it("every source has a base_url and docs_url", () => {
    for (const s of SOURCES) {
      expect(s.base_url).toBeTruthy();
      expect(s.docs_url).toBeTruthy();
    }
  });
});

describe("scoreToGrade", () => {
  it("maps low scores to A and high scores to F", () => {
    expect(scoreToGrade(5)).toBe("A");
    expect(scoreToGrade(35)).toBe("B");
    expect(scoreToGrade(55)).toBe("C");
    expect(scoreToGrade(75)).toBe("D");
    expect(scoreToGrade(95)).toBe("F");
  });

  it("clamps out-of-range scores", () => {
    expect(scoreToGrade(-10)).toBe("A");
    expect(scoreToGrade(1000)).toBe("F");
  });
});
