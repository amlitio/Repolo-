"use client";

import { useQuery } from "@tanstack/react-query";
import { getMapLayers } from "@/lib/api/endpoints";
import { queryKeys } from "./queryKeys";

export function useMapLayers() {
  return useQuery({
    queryKey: queryKeys.mapLayers(),
    queryFn: getMapLayers,
    staleTime: 5 * 60 * 1000,
  });
}
