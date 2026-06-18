"use client";

import { useQuery } from "@tanstack/react-query";
import { getAlerts, type GetAlertsParams } from "@/lib/api/endpoints";
import { queryKeys } from "./queryKeys";

export function useAlerts(params: GetAlertsParams = {}) {
  return useQuery({
    queryKey: queryKeys.alerts(params.countyFips, params.active),
    queryFn: () => getAlerts(params),
    staleTime: 60 * 1000,
    refetchInterval: 60 * 1000,
  });
}
