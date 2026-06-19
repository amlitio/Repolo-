"use client";

import { useQuery } from "@tanstack/react-query";
import { getProjects, type GetProjectsParams } from "@/lib/api/endpoints";
import { queryKeys } from "./queryKeys";

export function useProjects(params: GetProjectsParams = {}) {
  return useQuery({
    queryKey: queryKeys.projects(params.page),
    queryFn: () => getProjects(params),
  });
}
