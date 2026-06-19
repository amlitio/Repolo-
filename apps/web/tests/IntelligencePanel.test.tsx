import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { IntelligencePanel } from "@/components/map/IntelligencePanel";
import * as endpoints from "@/lib/api/endpoints";
import { ApiClientError } from "@/lib/api/client";
import type { CountyRiskScore } from "@firip/shared";

const COUNTY_RISK: CountyRiskScore = {
  county_fips: "12103",
  county_name: "Pinellas County",
  score: 72.4,
  grade: "C",
  factors: [
    { key: "storm_surge", label: "Storm surge exposure", weight: 0.4, raw_value: 3, normalized_score: 0.8, source_id: "noaa" },
  ],
  explanation: "Elevated risk driven by coastal storm surge exposure and low elevation.",
  model_version: "v1.0.0",
  computed_at: "2026-01-01T00:00:00Z",
};

function renderWithQueryClient(children: React.ReactNode) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(<QueryClientProvider client={queryClient}>{children}</QueryClientProvider>);
}

describe("IntelligencePanel", () => {
  it("shows an empty state when nothing is selected", () => {
    renderWithQueryClient(<IntelligencePanel selection={null} />);
    expect(screen.getByText("No selection")).toBeInTheDocument();
  });

  it("renders the county risk grade, score, and explanation once loaded", async () => {
    vi.spyOn(endpoints, "getCountyRisk").mockResolvedValue(COUNTY_RISK);
    renderWithQueryClient(
      <IntelligencePanel
        selection={{ type: "county", id: "12103", name: "Pinellas County", fips: "12103", centroid: [-82.7, 27.9] }}
      />
    );

    expect(await screen.findByText("Pinellas County")).toBeInTheDocument();
    expect(screen.getByText("C")).toBeInTheDocument();
    expect(screen.getByText("72.4")).toBeInTheDocument();
    expect(screen.getByText(/storm surge exposure and low elevation/i)).toBeInTheDocument();
    expect(screen.getByText("Storm surge exposure")).toBeInTheDocument();
  });

  it("renders an error state when the risk lookup fails (e.g. 404 unknown county)", async () => {
    vi.spyOn(endpoints, "getCountyRisk").mockRejectedValue(
      new ApiClientError({ code: "NOT_FOUND", message: "Unknown county", details: [], status: 404 })
    );
    renderWithQueryClient(
      <IntelligencePanel
        selection={{ type: "county", id: "99999", name: "Nowhere County", fips: "99999", centroid: [0, 0] }}
      />
    );

    expect(await screen.findByText(/could not load risk for nowhere county/i)).toBeInTheDocument();
  });
});
