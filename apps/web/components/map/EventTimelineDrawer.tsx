"use client";

import { useState } from "react";
import { useAlerts } from "@/lib/hooks/useAlerts";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/States";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils/cn";

const SEVERITY_VARIANT: Record<string, "danger" | "warning" | "default" | "outline"> = {
  Extreme: "danger",
  Severe: "danger",
  Moderate: "warning",
  Minor: "default",
  Unknown: "outline",
};

/** Bottom collapsible drawer: recent alerts/events. */
export function EventTimelineDrawer({ countyFips }: { countyFips?: string }) {
  const [collapsed, setCollapsed] = useState(true);
  const { data, isLoading, isError, error, refetch } = useAlerts({
    countyFips,
    active: true,
  });

  const count = data?.items.length ?? 0;

  return (
    <section
      aria-label="Event timeline"
      className={cn(
        "flex flex-col border-t border-slate-800 bg-slate-950 transition-[height]",
        collapsed ? "h-10" : "h-56"
      )}
    >
      <button
        type="button"
        onClick={() => setCollapsed((value) => !value)}
        aria-expanded={!collapsed}
        className="flex h-10 shrink-0 items-center justify-between px-3 text-left"
      >
        <span className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
          Event timeline
          {count > 0 ? (
            <Badge variant="warning">{count} active</Badge>
          ) : null}
        </span>
        <span className="font-mono text-[10px] text-slate-500">
          {collapsed ? "Expand" : "Collapse"}
        </span>
      </button>

      {!collapsed ? (
        <div className="flex-1 overflow-y-auto border-t border-slate-900 px-3 py-2">
          {isLoading ? <LoadingState label="Loading alerts…" /> : null}
          {isError ? (
            <ErrorState
              title="Failed to load alerts"
              description={error instanceof Error ? error.message : undefined}
              onRetry={() => refetch()}
            />
          ) : null}
          {!isLoading && !isError && count === 0 ? (
            <EmptyState title="No active alerts" description="All clear in this area." />
          ) : null}
          <ul className="space-y-2">
            {data?.items.map((alert) => (
              <li
                key={alert.id}
                className="flex items-start justify-between gap-3 rounded-sm border border-slate-900 bg-slate-900/40 px-2 py-1.5"
              >
                <div className="min-w-0 flex-1">
                  <p className="truncate text-xs font-medium text-slate-200">{alert.headline}</p>
                  <p className="truncate text-[11px] text-slate-500">{alert.area_desc}</p>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <Badge variant={SEVERITY_VARIANT[alert.severity] ?? "outline"}>
                    {alert.severity}
                  </Badge>
                  <span className="font-mono text-[10px] text-slate-600">
                    {new Date(alert.effective_at).toLocaleTimeString()}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {!collapsed ? (
        <div className="flex justify-end border-t border-slate-900 px-3 py-1.5">
          <Button size="sm" variant="ghost" onClick={() => refetch()}>
            Refresh
          </Button>
        </div>
      ) : null}
    </section>
  );
}
