"use client";

import { useQuery } from "@tanstack/react-query";
import { getWaterStations, type GetWaterStationsParams } from "@/lib/api/endpoints";
import { queryKeys } from "./queryKeys";

export function useWaterStations(params: GetWaterStationsParams = {}) {
  return useQuery({
    queryKey: queryKeys.waterStations(params.countyFips, params.sourceId),
    queryFn: () => getWaterStations(params),
  });
}
