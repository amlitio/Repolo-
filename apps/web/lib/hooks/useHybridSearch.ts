"use client";

import { useQuery } from "@tanstack/react-query";
import { hybridSearch } from "@/lib/api/endpoints";
import { queryKeys } from "./queryKeys";

export function useHybridSearch(q: string) {
  return useQuery({
    queryKey: queryKeys.hybridSearch(q),
    queryFn: () => hybridSearch({ q }),
    enabled: q.trim().length > 1,
  });
}
