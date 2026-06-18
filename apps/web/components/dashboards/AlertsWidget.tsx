"use client";

import { useAlerts } from "@/lib/hooks/useAlerts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/States";

const SEVERITY_VARIANT: Record<string, "danger" | "warning" | "default" | "outline"> = {
  Extreme: "danger",
  Severe: "danger",
  Moderate: "warning",
  Minor: "default",
  Unknown: "outline",
};

export function AlertsWidget({ countyFips }: { countyFips?: string }) {
  const { data, isLoading, isError, error, refetch } = useAlerts({ countyFips, active: true });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Active alerts</CardTitle>
        {data ? <Badge variant="outline">{data.total}</Badge> : null}
      </CardHeader>
      <CardContent>
        {isLoading ? <LoadingState label="Loading alerts…" /> : null}
        {isError ? (
          <ErrorState
            title="Failed to load alerts"
            description={error instanceof Error ? error.message : undefined}
            onRetry={() => refetch()}
          />
        ) : null}
        {!isLoading && !isError && data?.items.length === 0 ? (
          <EmptyState title="No active alerts" />
        ) : null}
        <ul className="space-y-1.5">
          {data?.items.slice(0, 6).map((alert) => (
            <li key={alert.id} className="flex items-center justify-between gap-2 text-xs">
              <span className="truncate text-slate-300">{alert.headline}</span>
              <Badge variant={SEVERITY_VARIANT[alert.severity] ?? "outline"}>
                {alert.severity}
              </Badge>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
