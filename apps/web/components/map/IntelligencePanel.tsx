"use client";

import { RiskGradeBadge } from "@/components/ui/RiskGradeBadge";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/States";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { usePropertyRisk } from "@/lib/hooks/usePropertyRisk";
import { useCountyRisk } from "@/lib/hooks/useCountyRisk";
import type { MapSearchResult } from "@/lib/api/endpoints";

export interface IntelligencePanelProps {
  selection: MapSearchResult | null;
}

/** Right panel: selected feature / search result risk score + explanation. */
export function IntelligencePanel({ selection }: IntelligencePanelProps) {
  return (
    <aside
      aria-label="Intelligence panel"
      className="flex h-full w-80 flex-col border-l border-slate-800 bg-slate-950"
    >
      <div className="border-b border-slate-800 px-3 py-2">
        <h2 className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
          Intelligence
        </h2>
      </div>

      <div className="flex-1 overflow-y-auto p-3">
        {!selection ? (
          <EmptyState
            title="No selection"
            description="Search or click a county/property on the map to see its risk profile."
          />
        ) : selection.type === "county" && selection.fips ? (
          <CountyRiskCard fips={selection.fips} name={selection.name} />
        ) : selection.type === "property" ? (
          <PropertyRiskCard propertyId={selection.id} name={selection.name} />
        ) : (
          <EmptyState title="Unsupported selection type" description={selection.type} />
        )}
      </div>
    </aside>
  );
}

function CountyRiskCard({ fips, name }: { fips: string; name: string }) {
  const { data, isLoading, isError, error, refetch } = useCountyRisk(fips);

  if (isLoading) return <LoadingState label={`Loading risk for ${name}…`} />;
  if (isError) {
    return (
      <ErrorState
        title={`Could not load risk for ${name}`}
        description={error instanceof Error ? error.message : undefined}
        onRetry={() => refetch()}
      />
    );
  }
  if (!data) return <EmptyState title="No risk data" />;

  return (
    <div className="space-y-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-sm font-semibold text-slate-100">{data.county_name}</p>
          <p className="font-mono text-[10px] text-slate-500">FIPS {data.county_fips}</p>
        </div>
        <RiskGradeBadge grade={data.grade} score={data.score} />
      </div>
      <p className="text-xs leading-relaxed text-slate-400">{data.explanation}</p>
      <FactorList factors={data.factors} />
      <p className="font-mono text-[10px] text-slate-600">
        Model {data.model_version} - computed {new Date(data.computed_at).toLocaleString()}
      </p>
    </div>
  );
}

function PropertyRiskCard({ propertyId, name }: { propertyId: string; name: string }) {
  const { data, isLoading, isError, error, refetch } = usePropertyRisk({ propertyId });

  if (isLoading) return <LoadingState label={`Loading risk for ${name}…`} />;
  if (isError) {
    return (
      <ErrorState
        title={`Could not load risk for ${name}`}
        description={error instanceof Error ? error.message : undefined}
        onRetry={() => refetch()}
      />
    );
  }
  if (!data) return <EmptyState title="No risk data" />;

  return (
    <div className="space-y-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-sm font-semibold text-slate-100">{name}</p>
          <p className="font-mono text-[10px] text-slate-500">{data.property_id}</p>
        </div>
        <RiskGradeBadge grade={data.grade} score={data.score} />
      </div>
      <p className="text-xs leading-relaxed text-slate-400">{data.explanation}</p>
      <FactorList factors={data.factors} />
      <p className="font-mono text-[10px] text-slate-600">
        Model {data.model_version} - computed {new Date(data.computed_at).toLocaleString()}
      </p>
    </div>
  );
}

function FactorList({
  factors,
}: {
  factors: { key: string; label: string; weight: number; normalized_score: number }[];
}) {
  if (factors.length === 0) return null;
  return (
    <Card>
      <CardHeader>
        <CardTitle>Factors</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {factors.map((factor) => (
          <div key={factor.key} className="space-y-1">
            <div className="flex items-center justify-between text-[11px] text-slate-300">
              <span>{factor.label}</span>
              <span className="font-mono text-slate-500">
                {(factor.normalized_score * 100).toFixed(0)}%
              </span>
            </div>
            <div className="h-1 w-full rounded-full bg-slate-800">
              <div
                className="h-1 rounded-full bg-cyan-500"
                style={{ width: `${Math.min(100, Math.max(0, factor.normalized_score * 100))}%` }}
              />
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
