"use client";

import { useQuery } from "@tanstack/react-query";
import {
  getProcurementOpportunities,
  type GetProcurementOpportunitiesParams,
} from "@/lib/api/endpoints";
import { queryKeys } from "./queryKeys";

export function useProcurementOpportunities(params: GetProcurementOpportunitiesParams = {}) {
  return useQuery({
    queryKey: queryKeys.procurementOpportunities(params.countyFips, params.q, params.page),
    queryFn: () => getProcurementOpportunities(params),
  });
}
