"use client";

import { useQuery } from "@tanstack/react-query";
import { getPropertyRisk, type GetPropertyRiskParams } from "@/lib/api/endpoints";
import { queryKeys } from "./queryKeys";

export function usePropertyRisk(params: GetPropertyRiskParams) {
  return useQuery({
    queryKey: queryKeys.propertyRisk(params.address, params.propertyId),
    queryFn: () => getPropertyRisk(params),
    enabled: Boolean(params.address || params.propertyId),
    retry: false,
  });
}
