"use client";

import { useQuery } from "@tanstack/react-query";
import { rankOpportunities } from "@/lib/api/endpoints";
import { queryKeys } from "./queryKeys";

export function useRankedOpportunities() {
  return useQuery({
    queryKey: queryKeys.rankedOpportunities(),
    queryFn: rankOpportunities,
  });
}
