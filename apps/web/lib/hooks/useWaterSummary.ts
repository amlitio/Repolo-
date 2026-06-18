"use client";

import { useQuery } from "@tanstack/react-query";
import { getWaterSummary } from "@/lib/api/endpoints";
import { queryKeys } from "./queryKeys";

export function useWaterSummary(countyFips: string | undefined) {
  return useQuery({
    queryKey: queryKeys.waterSummary(countyFips ?? ""),
    queryFn: () => getWaterSummary(countyFips as string),
    enabled: Boolean(countyFips),
  });
}
