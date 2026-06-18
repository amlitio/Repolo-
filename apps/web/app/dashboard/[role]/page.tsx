"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { COUNTIES } from "@firip/shared";
import {
  AlertsWidget,
  CountyRiskWidget,
  ProcurementWidget,
  ProjectsWidget,
  RankedOpportunitiesWidget,
  SubscriptionsWidget,
  WaterSummaryWidget,
  DASHBOARD_ROLE_DESCRIPTIONS,
  DASHBOARD_ROLE_LABELS,
  isDashboardRole,
  type DashboardRole,
} from "@/components/dashboards";
import { EmptyState } from "@/components/ui/States";

const SORTED_COUNTIES = [...COUNTIES].sort((a, b) => a.name.localeCompare(b.name));

export default function DashboardPage() {
  const params = useParams<{ role: string }>();
  const roleParam = params.role;
  const [countyFips, setCountyFips] = useState<string>("");

  if (!isDashboardRole(roleParam)) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950 p-6">
        <EmptyState
          title="Unknown dashboard"
          description={`"${roleParam}" is not a recognized dashboard role.`}
        />
      </main>
    );
  }

  const role = roleParam;

  return (
    <main className="min-h-screen bg-slate-950 p-6">
      <header className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="font-mono text-[11px] uppercase tracking-widest text-cyan-400">
            Dashboard
          </p>
          <h1 className="text-xl font-semibold text-slate-100">
            {DASHBOARD_ROLE_LABELS[role]}
          </h1>
          <p className="mt-1 max-w-xl text-xs text-slate-500">
            {DASHBOARD_ROLE_DESCRIPTIONS[role]}
          </p>
        </div>

        <label className="flex items-center gap-2 text-xs text-slate-400">
          County
          <select
            value={countyFips}
            onChange={(event) => setCountyFips(event.target.value)}
            className="h-8 rounded-sm border border-slate-700 bg-slate-950 px-2 text-xs text-slate-100"
          >
            <option value="">Select a county…</option>
            {SORTED_COUNTIES.map((county) => (
              <option key={county.fips} value={county.fips}>
                {county.name}
              </option>
            ))}
          </select>
        </label>
      </header>

      <DashboardWidgets role={role} countyFips={countyFips || undefined} />
    </main>
  );
}

function DashboardWidgets({
  role,
  countyFips,
}: {
  role: DashboardRole;
  countyFips: string | undefined;
}) {
  const grid = "grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3";

  switch (role) {
    case "executive":
      return (
        <div className={grid}>
          {countyFips ? <CountyRiskWidget countyFips={countyFips} /> : <NoCountySelected />}
          <AlertsWidget countyFips={countyFips} />
          <ProjectsWidget />
        </div>
      );
    case "government":
      return (
        <div className={grid}>
          {countyFips ? <CountyRiskWidget countyFips={countyFips} /> : <NoCountySelected />}
          {countyFips ? <WaterSummaryWidget countyFips={countyFips} /> : <NoCountySelected />}
          <AlertsWidget countyFips={countyFips} />
        </div>
      );
    case "engineering":
      return (
        <div className={grid}>
          {countyFips ? <WaterSummaryWidget countyFips={countyFips} /> : <NoCountySelected />}
          {countyFips ? <CountyRiskWidget countyFips={countyFips} /> : <NoCountySelected />}
          <ProjectsWidget />
        </div>
      );
    case "contractor":
      return (
        <div className={grid}>
          <ProcurementWidget countyFips={countyFips} />
          <RankedOpportunitiesWidget />
          <ProjectsWidget />
        </div>
      );
    case "investor":
      return (
        <div className={grid}>
          {countyFips ? <CountyRiskWidget countyFips={countyFips} /> : <NoCountySelected />}
          <ProcurementWidget countyFips={countyFips} />
          <ProjectsWidget />
        </div>
      );
    case "emergency-management":
      return (
        <div className={grid}>
          <AlertsWidget countyFips={countyFips} />
          {countyFips ? <CountyRiskWidget countyFips={countyFips} /> : <NoCountySelected />}
          <SubscriptionsWidget defaultCountyFips={countyFips} />
        </div>
      );
    default:
      return null;
  }
}

function NoCountySelected() {
  return <EmptyState title="Select a county" description="Choose a county above to load this widget." />;
}
