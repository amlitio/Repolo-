"use client";

import { useEffect, useRef, useState } from "react";
import type { Map as MapboxMap } from "mapbox-gl";
import { MAP_LAYER_IDS, type MapLayerDefinition } from "@firip/shared";

const FLORIDA_CENTER: [number, number] = [-81.5158, 27.6648];
const FLORIDA_ZOOM = 6.2;

/** Dark "Bloomberg terminal" basemap style. */
const DARK_STYLE = "mapbox://styles/mapbox/dark-v11";

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

  // Layer add/remove driven by LayerManager state. Each MapLayerDefinition
  // is expected to back a mapbox source+layer pair once apps/api serves
  // real GeoJSON via /map/features/query; for now this wiring is a no-op
  // beyond toggling visibility on layers that already exist on the map
  // instance, since tile/source registration depends on live data.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || status !== "ready") return;

    for (const layer of layers) {
      if (!map.getLayer(layer.id)) continue;
      const visibility = visibleLayerIds.includes(layer.id) ? "visible" : "none";
      map.setLayoutProperty(layer.id, "visibility", visibility);
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
