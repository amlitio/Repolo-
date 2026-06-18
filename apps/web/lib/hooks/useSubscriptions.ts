"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createSubscription,
  listSubscriptions,
  sendTestNotification,
  type CreateSubscriptionPayload,
} from "@/lib/api/endpoints";
import { queryKeys } from "./queryKeys";

export function useSubscriptions() {
  return useQuery({
    queryKey: queryKeys.subscriptions(),
    queryFn: listSubscriptions,
  });
}

export function useCreateSubscription() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateSubscriptionPayload) => createSubscription(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.subscriptions() });
    },
  });
}

export function useSendTestNotification() {
  return useMutation({
    mutationFn: sendTestNotification,
  });
}
