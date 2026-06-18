"use client";

import { useQuery } from "@tanstack/react-query";
import { getCountyRisk } from "@/lib/api/endpoints";
import { queryKeys } from "./queryKeys";

export function useCountyRisk(fips: string | undefined) {
  return useQuery({
    queryKey: queryKeys.countyRisk(fips ?? ""),
    queryFn: () => getCountyRisk(fips as string),
    enabled: Boolean(fips),
    retry: false,
  });
}
