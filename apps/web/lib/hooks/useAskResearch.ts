"use client";

import { useMutation } from "@tanstack/react-query";
import { askResearch, type AskResearchPayload } from "@/lib/api/endpoints";

export function useAskResearch() {
  return useMutation({
    mutationFn: (payload: AskResearchPayload) => askResearch(payload),
  });
}
