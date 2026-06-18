"use client";

import { useEffect, useState } from "react";
import { MapCanvas } from "@/components/map/MapCanvas";
import { LayerManager } from "@/components/map/LayerManager";
import { IntelligencePanel } from "@/components/map/IntelligencePanel";
import { EventTimelineDrawer } from "@/components/map/EventTimelineDrawer";
import { SearchBar } from "@/components/map/SearchBar";
import { useMapLayers } from "@/lib/hooks/useMapLayers";
import type { MapSearchResult } from "@/lib/api/endpoints";

export default function MapWorkspacePage() {
  const { data: layers } = useMapLayers();
  const [visibleLayerIds, setVisibleLayerIds] = useState<string[]>([]);
  const [defaultsSeeded, setDefaultsSeeded] = useState(false);
  const [selection, setSelection] = useState<MapSearchResult | null>(null);

  // Seed default-visible layers once layer defs arrive (once only - after
  // that, the user's own toggles are the source of truth).
  useEffect(() => {
    if (!layers || defaultsSeeded) return;
    const defaults = layers.filter((layer) => layer.default_visible).map((layer) => layer.id);
    setVisibleLayerIds(defaults);
    setDefaultsSeeded(true);
  }, [layers, defaultsSeeded]);

  function handleToggleLayer(layerId: string, visible: boolean) {
    setVisibleLayerIds((current) =>
      visible ? [...current, layerId] : current.filter((id) => id !== layerId)
    );
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
