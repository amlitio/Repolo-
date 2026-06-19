"use client";

import { useQuery } from "@tanstack/react-query";
import { searchMap } from "@/lib/api/endpoints";
import { queryKeys } from "./queryKeys";

export function useMapSearch(q: string) {
  return useQuery({
    queryKey: queryKeys.mapSearch(q),
    queryFn: () => searchMap(q),
    enabled: q.trim().length > 1,
    staleTime: 30 * 1000,
  });
}
