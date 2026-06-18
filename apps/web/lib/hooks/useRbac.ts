"use client";

import { useQuery } from "@tanstack/react-query";
import { getRbacMe, getSession, getOrgs } from "@/lib/api/endpoints";
import { queryKeys } from "./queryKeys";

export function useRbacMe() {
  return useQuery({
    queryKey: queryKeys.rbacMe(),
    queryFn: getRbacMe,
    retry: false,
  });
}

export function useSession() {
  return useQuery({
    queryKey: queryKeys.session(),
    queryFn: getSession,
    retry: false,
  });
}

export function useOrgs() {
  return useQuery({
    queryKey: queryKeys.orgs(),
    queryFn: getOrgs,
    retry: false,
  });
}
