"use client";

import { useQuery } from "@tanstack/react-query";
import { explainRisk, type ExplainRiskParams } from "@/lib/api/endpoints";
import { queryKeys } from "./queryKeys";

export function useRiskExplain(params: ExplainRiskParams) {
  return useQuery({
    queryKey: queryKeys.riskExplain(params.propertyId, params.countyFips),
    queryFn: () => explainRisk(params),
    enabled: Boolean(params.propertyId || params.countyFips),
  });
}
