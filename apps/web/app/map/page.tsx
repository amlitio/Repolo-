"use client";

import { useMemo, useState } from "react";
import { MapCanvas } from "@/components/map/MapCanvas";
import { LayerManager } from "@/components/map/LayerManager";
import { IntelligencePanel } from "@/components/map/IntelligencePanel";
import { EventTimelineDrawer } from "@/components/map/EventTimelineDrawer";
import { SearchBar } from "@/components/map/SearchBar";
import { useMapLayers } from "@/lib/hooks/useMapLayers";
import type { MapSearchResult } from "@/lib/api/endpoints";

export default function MapWorkspacePage() {
  const { data: layers } = useMapLayers();
  // `null` means "no manual toggles yet" - in that state visibility is
  // derived straight from each layer's `default_visible` flag once `layers`
  // arrives, with no effect/setState round-trip needed. The first manual
  // toggle materializes an explicit id array that takes over as the source
  // of truth from then on.
  const [manualVisibleLayerIds, setManualVisibleLayerIds] = useState<string[] | null>(null);
  const [selection, setSelection] = useState<MapSearchResult | null>(null);

  const defaultVisibleLayerIds = useMemo(
    () => (layers ?? []).filter((layer) => layer.default_visible).map((layer) => layer.id),
    [layers]
  );
  const visibleLayerIds = manualVisibleLayerIds ?? defaultVisibleLayerIds;

  function handleToggleLayer(layerId: string, visible: boolean) {
    setManualVisibleLayerIds((current) => {
      const base = current ?? defaultVisibleLayerIds;
      return visible ? [...base, layerId] : base.filter((id) => id !== layerId);
    });
  }

  const flyTo = selection ? { center: selection.centroid, zoom: 11 } : null;

  return (
    <div className="grid h-screen grid-cols-[16rem_1fr_20rem] grid-rows-[auto_1fr_auto] bg-slate-950">
      <div className="col-span-3">
        <SearchBar onSelectResult={setSelection} />
      </div>

      <LayerManager visibleLayerIds={visibleLayerIds} onToggle={handleToggleLayer} />

      <main className="relative h-full w-full overflow-hidden">
        <MapCanvas
          visibleLayerIds={visibleLayerIds}
          layers={layers ?? []}
          flyTo={flyTo}
        />
      </main>

      <IntelligencePanel selection={selection} />

      <div className="col-span-3">
        <EventTimelineDrawer countyFips={selection?.fips ?? undefined} />
      </div>
    </div>
  );
}
