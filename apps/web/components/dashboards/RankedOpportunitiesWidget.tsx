"use client";

import { useRankedOpportunities } from "@/lib/hooks/useRankedOpportunities";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/States";

export function RankedOpportunitiesWidget() {
  const { data, isLoading, isError, error, refetch } = useRankedOpportunities();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Ranked opportunities</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? <LoadingState label="Loading ranked opportunities…" /> : null}
        {isError ? (
          <ErrorState
            title="Failed to load ranked opportunities"
            description={error instanceof Error ? error.message : undefined}
            onRetry={() => refetch()}
          />
        ) : null}
        {!isLoading && !isError && data?.length === 0 ? (
          <EmptyState title="Scaffold has no results yet" />
        ) : null}
        <ol className="space-y-1.5">
          {data?.slice(0, 6).map((opportunity, index) => (
            <li key={opportunity.id} className="flex items-center justify-between text-xs text-slate-300">
              <span className="truncate">
                <span className="mr-1.5 font-mono text-slate-500">{index + 1}.</span>
                {opportunity.title}
              </span>
              <span className="font-mono text-[10px] text-slate-500">
                {opportunity.score.toFixed(2)}
              </span>
            </li>
          ))}
        </ol>
      </CardContent>
    </Card>
  );
}
