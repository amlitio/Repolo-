"use client";

import { useQuery } from "@tanstack/react-query";
import {
  adminListAuditLogs,
  adminListIngestionRuns,
  adminListSources,
} from "@/lib/api/endpoints";
import { queryKeys } from "./queryKeys";

export function useAdminSources(page?: number) {
  return useQuery({
    queryKey: queryKeys.adminSources(page),
    queryFn: () => adminListSources({ page }),
  });
}

export function useAdminIngestionRuns(sourceId?: string) {
  return useQuery({
    queryKey: queryKeys.adminIngestionRuns(sourceId),
    queryFn: () => adminListIngestionRuns({ sourceId }),
  });
}

export function useAdminAuditLogs(page?: number) {
  return useQuery({
    queryKey: queryKeys.adminAuditLogs(page),
    queryFn: () => adminListAuditLogs({ page }),
  });
}
