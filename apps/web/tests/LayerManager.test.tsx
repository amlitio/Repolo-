import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { LayerManager } from "@/components/map/LayerManager";
import * as endpoints from "@/lib/api/endpoints";
import type { MapLayerDefinition } from "@firip/shared";

const LAYERS: MapLayerDefinition[] = [
  {
    id: "fema-flood-zones",
    name: "FEMA Flood Zones",
    category: "flood",
    source_id: "fema-nfhl",
    default_visible: true,
    min_zoom: 0,
    max_zoom: 22,
    legend: [{ label: "SFHA", color: "#ef4444" }],
  },
  {
    id: "usgs-water-stations",
    name: "USGS Water Stations",
    category: "water",
    source_id: "usgs-nwis",
    default_visible: false,
    min_zoom: 0,
    max_zoom: 22,
    legend: [{ label: "Station", color: "#22d3ee" }],
  },
];

function renderWithQueryClient(children: React.ReactNode) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(<QueryClientProvider client={queryClient}>{children}</QueryClientProvider>);
}

describe("LayerManager", () => {
  beforeEach(() => {
    vi.spyOn(endpoints, "getMapLayers").mockResolvedValue(LAYERS);
  });

  it("renders a checkbox per layer, grouped by category", async () => {
    renderWithQueryClient(<LayerManager visibleLayerIds={[]} onToggle={vi.fn()} />);

    expect(await screen.findByText("FEMA Flood Zones")).toBeInTheDocument();
    expect(screen.getByText("USGS Water Stations")).toBeInTheDocument();
    expect(screen.getByText("Flood")).toBeInTheDocument();
    expect(screen.getByText("Water")).toBeInTheDocument();
  });

  it("reflects visibleLayerIds in checkbox checked state", async () => {
    renderWithQueryClient(
      <LayerManager visibleLayerIds={["fema-flood-zones"]} onToggle={vi.fn()} />
    );

    const floodCheckbox = await screen.findByRole("checkbox", { name: /FEMA Flood Zones/i });
    const waterCheckbox = screen.getByRole("checkbox", { name: /USGS Water Stations/i });

    expect(floodCheckbox).toBeChecked();
    expect(waterCheckbox).not.toBeChecked();
  });

  it("calls onToggle with the layer id and new checked state when clicked", async () => {
    const onToggle = vi.fn();
    const user = userEvent.setup();
    renderWithQueryClient(<LayerManager visibleLayerIds={[]} onToggle={onToggle} />);

    const floodCheckbox = await screen.findByRole("checkbox", { name: /FEMA Flood Zones/i });
    await user.click(floodCheckbox);

    await waitFor(() => {
      expect(onToggle).toHaveBeenCalledWith("fema-flood-zones", true);
    });
  });

  it("shows an empty state when no layers are returned", async () => {
    vi.spyOn(endpoints, "getMapLayers").mockResolvedValue([]);
    renderWithQueryClient(<LayerManager visibleLayerIds={[]} onToggle={vi.fn()} />);

    expect(await screen.findByText("No layers available")).toBeInTheDocument();
  });
});
