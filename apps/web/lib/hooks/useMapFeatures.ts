"use client";

import { useQueries } from "@tanstack/react-query";
import { queryMapFeatures } from "@/lib/api/endpoints";
import { queryKeys } from "./queryKeys";

export interface MapFeatureResult {
  layerId: string;
  data: GeoJSON.FeatureCollection | undefined;
  isLoading: boolean;
  isError: boolean;
}

/**
 * Fetches the GeoJSON FeatureCollection for each given layer id in
 * parallel via GET /map/features/query, cached per layer+bbox+zoom so
 * toggling a layer's visibility never re-fetches data already in hand.
 */
export function useMapFeatures(
  layerIds: string[],
  bbox: [number, number, number, number],
  zoom?: number
): MapFeatureResult[] {
  const results = useQueries({
    queries: layerIds.map((layerId) => ({
      queryKey: queryKeys.mapFeatures(layerId, bbox, zoom),
      queryFn: () => queryMapFeatures({ layerId, bbox, zoom }),
      staleTime: 5 * 60 * 1000,
    })),
  });

  return layerIds.map((layerId, index) => ({
    layerId,
    data: results[index]?.data as GeoJSON.FeatureCollection | undefined,
    isLoading: results[index]?.isLoading ?? false,
    isError: results[index]?.isError ?? false,
  }));
}
