"use client";

import { useEffect, useRef, useState } from "react";
import type { GeoJSONSource, Map as MapboxMap } from "mapbox-gl";
import { MAP_LAYER_IDS, type MapLayerDefinition } from "@firip/shared";
import { useMapFeatures } from "@/lib/hooks/useMapFeatures";

const FLORIDA_CENTER: [number, number] = [-81.5158, 27.6648];
const FLORIDA_ZOOM = 6.2;

/** Bounding box covering all of Florida including the Keys - used for every
 * /map/features/query call so layer data is fetched once and cached rather
 * than re-fetched on every pan (most layer geometries aren't even
 * bbox-filtered server-side; see apps/api/app/routers/map.py). */
const FLORIDA_BBOX: [number, number, number, number] = [-87.7, 24.4, -79.8, 31.1];

/** Dark "Bloomberg terminal" basemap style. */
const DARK_STYLE = "mapbox://styles/mapbox/dark-v11";

/** Mapbox layer ids backing one MapLayerDefinition's source - polygon
 * categories render as a fill+outline pair, everything else is a single layer. */
function mapboxLayerIdsFor(layer: MapLayerDefinition): string[] {
  switch (layer.category) {
    case "water":
    case "procurement":
    case "hurricane":
    case "boundary":
      return [layer.id];
    default:
      return [`${layer.id}-fill`, `${layer.id}-line`];
  }
}

/** Adds the paint layer(s) for a freshly-registered GeoJSON source, styled by geometry shape. */
function addLayerToMap(map: MapboxMap, layer: MapLayerDefinition) {
  const color = layer.legend[0]?.color ?? "#38bdf8";
  const zoomRange = { minzoom: layer.min_zoom, maxzoom: layer.max_zoom };

  switch (layer.category) {
    case "water":
    case "procurement":
      map.addLayer({
        id: layer.id,
        type: "circle",
        source: layer.id,
        ...zoomRange,
        paint: {
          "circle-radius": 5,
          "circle-color": color,
          "circle-stroke-width": 1,
          "circle-stroke-color": "#0f172a",
        },
      });
      return;
    case "hurricane":
    case "boundary":
      map.addLayer({
        id: layer.id,
        type: "line",
        source: layer.id,
        ...zoomRange,
        paint: {
          "line-color": color,
          "line-width": 2,
        },
      });
      return;
    default:
      map.addLayer({
        id: `${layer.id}-fill`,
        type: "fill",
        source: layer.id,
        ...zoomRange,
        paint: {
          "fill-color": color,
          "fill-opacity": 0.35,
        },
      });
      map.addLayer({
        id: `${layer.id}-line`,
        type: "line",
        source: layer.id,
        ...zoomRange,
        paint: {
          "line-color": color,
          "line-width": 1,
        },
      });
  }
}

export interface MapCanvasProps {
  visibleLayerIds: string[];
  layers: MapLayerDefinition[];
  onFeatureSelect?: (feature: { layerId: string; properties: Record<string, unknown> }) => void;
  flyTo?: { center: [number, number]; zoom?: number } | null;
}

/**
 * Mapbox GL JS wrapper. Degrades to a clear placeholder (rather than
 * crashing) when NEXT_PUBLIC_MAPBOX_TOKEN is unset or the mapbox-gl script
 * fails to initialize - this sandbox has no network access to
 * api.mapbox.com, and production deploys without a token should fail
 * loudly but gracefully, not blank-screen.
 */
export function MapCanvas({ visibleLayerIds, layers, flyTo }: MapCanvasProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MapboxMap | null>(null);
  const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;

  // "no-token" is derived directly from env at render time rather than set
  // via an effect - it's not the result of any async work, so there's no
  // reason to round-trip it through state-after-mount.
  const [status, setStatus] = useState<"loading" | "ready" | "error" | "no-token">(
    token ? "loading" : "no-token"
  );
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const layerIds = layers.map((layer) => layer.id);
  const featureResults = useMapFeatures(layerIds, FLORIDA_BBOX);

  useEffect(() => {
    if (!token) return;
    if (!containerRef.current || mapRef.current) return;

    let cancelled = false;

    import("mapbox-gl")
      .then((mapboxgl) => {
        if (cancelled || !containerRef.current) return;
        mapboxgl.default.accessToken = token;

        const map = new mapboxgl.default.Map({
          container: containerRef.current,
          style: DARK_STYLE,
          center: FLORIDA_CENTER,
          zoom: FLORIDA_ZOOM,
          attributionControl: true,
        });

        map.addControl(new mapboxgl.default.NavigationControl(), "top-right");

        map.on("load", () => {
          if (cancelled) return;
          setStatus("ready");
        });

        map.on("error", (event) => {
          if (cancelled) return;
          setErrorMessage(event.error?.message ?? "Map failed to load");
          setStatus("error");
        });

        mapRef.current = map;
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setErrorMessage(error instanceof Error ? error.message : "Failed to load Mapbox GL JS");
        setStatus("error");
      });

    return () => {
      cancelled = true;
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, [token]);

  useEffect(() => {
    if (!flyTo || status !== "ready" || !mapRef.current) return;
    mapRef.current.flyTo({ center: flyTo.center, zoom: flyTo.zoom ?? 11 });
  }, [flyTo, status]);

  // Registers a GeoJSON source + paint layer(s) for each layer's data as it
  // arrives from useMapFeatures, and pushes updated data into the source if
  // it's already registered (e.g. after a query refetch).
  useEffect(() => {
    const map = mapRef.current;
    if (!map || status !== "ready") return;

    for (const layer of layers) {
      const result = featureResults.find((r) => r.layerId === layer.id);
      if (!result?.data) continue;

      const existingSource = map.getSource(layer.id) as GeoJSONSource | undefined;
      if (existingSource) {
        existingSource.setData(result.data);
        continue;
      }

      map.addSource(layer.id, { type: "geojson", data: result.data });
      addLayerToMap(map, layer);
      const visibility = visibleLayerIds.includes(layer.id) ? "visible" : "none";
      for (const id of mapboxLayerIdsFor(layer)) {
        map.setLayoutProperty(id, "visibility", visibility);
      }
    }
  }, [layers, featureResults, status, visibleLayerIds]);

  // Layer visibility driven by LayerManager state, applied to layers that
  // already have a registered source (see effect above).
  useEffect(() => {
    const map = mapRef.current;
    if (!map || status !== "ready") return;

    for (const layer of layers) {
      const visibility = visibleLayerIds.includes(layer.id) ? "visible" : "none";
      for (const id of mapboxLayerIdsFor(layer)) {
        if (!map.getLayer(id)) continue;
        map.setLayoutProperty(id, "visibility", visibility);
      }
    }
  }, [visibleLayerIds, layers, status]);

  if (status === "no-token") {
    return (
      <MapPlaceholder
        title="Map disabled"
        message="Set NEXT_PUBLIC_MAPBOX_TOKEN to load the map."
      />
    );
  }

  if (status === "error") {
    return (
      <MapPlaceholder
        title="Map failed to load"
        message={errorMessage ?? "Check NEXT_PUBLIC_MAPBOX_TOKEN and network access to Mapbox."}
      />
    );
  }

  return (
    <div className="relative h-full w-full bg-slate-950">
      <div ref={containerRef} data-testid="mapbox-container" className="h-full w-full" />
      {status === "loading" ? (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-950/80">
          <p className="font-mono text-xs text-slate-500">Loading map…</p>
        </div>
      ) : null}
    </div>
  );
}

function MapPlaceholder({ title, message }: { title: string; message: string }) {
  return (
    <div
      data-testid="map-placeholder"
      className="flex h-full w-full flex-col items-center justify-center gap-2 bg-[radial-gradient(circle_at_center,_#0f172a,_#020617)] text-center"
    >
      <span className="font-mono text-xs uppercase tracking-widest text-slate-500">{title}</span>
      <p className="max-w-sm text-sm text-slate-400">{message}</p>
    </div>
  );
}

export const ALL_LAYER_IDS = Object.values(MAP_LAYER_IDS);
