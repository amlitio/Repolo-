"use client";

import { useWaterSummary } from "@/lib/hooks/useWaterSummary";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/States";

export function WaterSummaryWidget({ countyFips }: { countyFips: string }) {
  const { data, isLoading, isError, error, refetch } = useWaterSummary(countyFips);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Water summary</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? <LoadingState label="Loading water summary…" /> : null}
        {isError ? (
          <ErrorState
            title="Failed to load water summary"
            description={error instanceof Error ? error.message : undefined}
            onRetry={() => refetch()}
          />
        ) : null}
        {!isLoading && !isError && !data ? <EmptyState title="No station data" /> : null}
        {data ? (
          <dl className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <dt className="text-slate-500">Stations</dt>
              <dd className="font-mono text-slate-100">{data.station_count}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Trend</dt>
              <dd className="font-mono text-slate-100">{data.trend}</dd>
            </div>
          </dl>
        ) : null}
      </CardContent>
    </Card>
  );
}
