"use client";

import { useProcurementOpportunities } from "@/lib/hooks/useProcurementOpportunities";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/States";

export function ProcurementWidget({ countyFips }: { countyFips?: string }) {
  const { data, isLoading, isError, error, refetch } = useProcurementOpportunities({
    countyFips,
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Procurement opportunities</CardTitle>
        {data ? <Badge variant="outline">{data.total}</Badge> : null}
      </CardHeader>
      <CardContent>
        {isLoading ? <LoadingState label="Loading opportunities…" /> : null}
        {isError ? (
          <ErrorState
            title="Failed to load opportunities"
            description={error instanceof Error ? error.message : undefined}
            onRetry={() => refetch()}
          />
        ) : null}
        {!isLoading && !isError && data?.items.length === 0 ? (
          <EmptyState
            title="No opportunities yet"
            description="Procurement ingestion is pending for this view."
          />
        ) : null}
        <ul className="space-y-1.5">
          {data?.items.slice(0, 6).map((opportunity) => (
            <li key={opportunity.id} className="text-xs text-slate-300">
              <p className="truncate font-medium">{opportunity.title}</p>
              {opportunity.agency ? (
                <p className="truncate text-[11px] text-slate-500">{opportunity.agency}</p>
              ) : null}
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
