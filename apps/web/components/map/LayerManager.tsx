"use client";

import type { MapLayerDefinition } from "@firip/shared";
import { useMapLayers } from "@/lib/hooks/useMapLayers";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/States";
import { cn } from "@/lib/utils/cn";

export interface LayerManagerProps {
  visibleLayerIds: string[];
  onToggle: (layerId: string, visible: boolean) => void;
}

const CATEGORY_LABELS: Record<MapLayerDefinition["category"], string> = {
  flood: "Flood",
  weather: "Weather",
  water: "Water",
  risk: "Risk",
  hurricane: "Hurricane",
  procurement: "Procurement",
  boundary: "Boundaries",
};

/** Left panel: toggles for each MapLayerDefinition returned by GET /map/layers. */
export function LayerManager({ visibleLayerIds, onToggle }: LayerManagerProps) {
  const { data: layers, isLoading, isError, error, refetch } = useMapLayers();

  return (
    <aside
      aria-label="Layer manager"
      className="flex h-full w-64 flex-col border-r border-slate-800 bg-slate-950"
    >
      <div className="border-b border-slate-800 px-3 py-2">
        <h2 className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
          Layers
        </h2>
      </div>

      <div className="flex-1 overflow-y-auto">
        {isLoading ? <LoadingState label="Loading layers…" /> : null}
        {isError ? (
          <ErrorState
            title="Failed to load layers"
            description={error instanceof Error ? error.message : undefined}
            onRetry={() => refetch()}
          />
        ) : null}
        {!isLoading && !isError && layers?.length === 0 ? (
          <EmptyState title="No layers available" />
        ) : null}

        {layers && layers.length > 0
          ? groupByCategory(layers).map(([category, categoryLayers]) => (
              <div key={category} className="border-b border-slate-900">
                <p className="px-3 pt-2 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
                  {CATEGORY_LABELS[category] ?? category}
                </p>
                <ul className="px-1 pb-2">
                  {categoryLayers.map((layer) => {
                    const checked = visibleLayerIds.includes(layer.id);
                    return (
                      <li key={layer.id}>
                        <label
                          className={cn(
                            "flex cursor-pointer items-center gap-2 rounded-sm px-2 py-1.5 text-xs text-slate-300 hover:bg-slate-900",
                            checked && "text-slate-100"
                          )}
                        >
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={(event) => onToggle(layer.id, event.target.checked)}
                            className="h-3.5 w-3.5 accent-cyan-500"
                          />
                          <span className="flex-1 truncate">{layer.name}</span>
                          {layer.legend[0] ? (
                            <span
                              aria-hidden
                              className="h-2.5 w-2.5 rounded-full border border-slate-700"
                              style={{ backgroundColor: layer.legend[0].color }}
                            />
                          ) : null}
                        </label>
                      </li>
                    );
                  })}
                </ul>
              </div>
            ))
          : null}
      </div>
    </aside>
  );
}

function groupByCategory(
  layers: MapLayerDefinition[]
): [MapLayerDefinition["category"], MapLayerDefinition[]][] {
  const groups = new Map<MapLayerDefinition["category"], MapLayerDefinition[]>();
  for (const layer of layers) {
    const existing = groups.get(layer.category);
    if (existing) {
      existing.push(layer);
    } else {
      groups.set(layer.category, [layer]);
    }
  }
  return Array.from(groups.entries());
}
