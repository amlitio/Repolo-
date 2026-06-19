"use client";

import { useCountyRisk } from "@/lib/hooks/useCountyRisk";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { RiskGradeBadge } from "@/components/ui/RiskGradeBadge";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/States";

export function CountyRiskWidget({ countyFips }: { countyFips: string }) {
  const { data, isLoading, isError, error, refetch } = useCountyRisk(countyFips);

  return (
    <Card>
      <CardHeader>
        <CardTitle>County risk</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? <LoadingState label="Loading county risk…" /> : null}
        {isError ? (
          <ErrorState
            title="Failed to load county risk"
            description={error instanceof Error ? error.message : undefined}
            onRetry={() => refetch()}
          />
        ) : null}
        {!isLoading && !isError && !data ? <EmptyState title="No risk score available" /> : null}
        {data ? (
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-100">{data.county_name}</p>
              <p className="font-mono text-[10px] text-slate-500">FIPS {data.county_fips}</p>
            </div>
            <RiskGradeBadge grade={data.grade} score={data.score} />
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
