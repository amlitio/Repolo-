"use client";

import { useState } from "react";
import { useRbacMe } from "@/lib/hooks/useRbac";
import { useAdminAuditLogs, useAdminIngestionRuns, useAdminSources } from "@/lib/hooks/useAdmin";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/Tabs";
import { Badge } from "@/components/ui/Badge";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/States";

const ADMIN_ROLE = "admin";

export default function AdminPage() {
  const { data: rbac, isLoading, isError } = useRbacMe();

  if (isLoading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950">
        <LoadingState label="Checking permissions…" />
      </main>
    );
  }

  if (isError || !rbac || rbac.role !== ADMIN_ROLE) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950 p-6">
        <EmptyState
          title="Insufficient permissions"
          description="This view requires the admin role. Contact your organization owner if you believe this is an error."
        />
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-950 p-6">
      <header className="mb-6">
        <p className="font-mono text-[11px] uppercase tracking-widest text-cyan-400">Admin</p>
        <h1 className="text-xl font-semibold text-slate-100">Data &amp; Audit Console</h1>
      </header>

      <Tabs defaultValue="sources">
        <TabsList>
          <TabsTrigger value="sources">Sources</TabsTrigger>
          <TabsTrigger value="ingestion-runs">Ingestion runs</TabsTrigger>
          <TabsTrigger value="audit-logs">Audit logs</TabsTrigger>
        </TabsList>

        <TabsContent value="sources">
          <SourcesTable />
        </TabsContent>
        <TabsContent value="ingestion-runs">
          <IngestionRunsTable />
        </TabsContent>
        <TabsContent value="audit-logs">
          <AuditLogsTable />
        </TabsContent>
      </Tabs>
    </main>
  );
}

function SourcesTable() {
  const { data, isLoading, isError, error, refetch } = useAdminSources();

  if (isLoading) return <LoadingState label="Loading sources…" />;
  if (isError) {
    return (
      <ErrorState
        title="Failed to load sources"
        description={error instanceof Error ? error.message : undefined}
        onRetry={() => refetch()}
      />
    );
  }
  if (!data || data.length === 0) return <EmptyState title="No sources registered" />;

  return (
    <table className="w-full text-left text-xs">
      <thead>
        <tr className="border-b border-slate-800 text-slate-500">
          <th className="py-1.5 pr-3 font-medium">Name</th>
          <th className="py-1.5 pr-3 font-medium">Agency</th>
          <th className="py-1.5 pr-3 font-medium">Level</th>
          <th className="py-1.5 pr-3 font-medium">Quality</th>
        </tr>
      </thead>
      <tbody>
        {data.map((source) => (
          <tr key={source.id} className="border-b border-slate-900 text-slate-300">
            <td className="py-1.5 pr-3">{source.name}</td>
            <td className="py-1.5 pr-3">{source.agency}</td>
            <td className="py-1.5 pr-3">{source.level}</td>
            <td className="py-1.5 pr-3">
              <Badge variant={source.data_quality_status === "verified" ? "success" : "outline"}>
                {source.data_quality_status}
              </Badge>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function IngestionRunsTable() {
  const [sourceId, setSourceId] = useState("");
  const { data, isLoading, isError, error, refetch } = useAdminIngestionRuns(
    sourceId || undefined
  );

  return (
    <div className="space-y-2">
      <input
        value={sourceId}
        onChange={(event) => setSourceId(event.target.value)}
        placeholder="Filter by source id…"
        className="h-8 w-64 rounded-sm border border-slate-700 bg-slate-950 px-2 text-xs text-slate-100"
      />
      {isLoading ? <LoadingState label="Loading ingestion runs…" /> : null}
      {isError ? (
        <ErrorState
          title="Failed to load ingestion runs"
          description={error instanceof Error ? error.message : undefined}
          onRetry={() => refetch()}
        />
      ) : null}
      {!isLoading && !isError && data?.items.length === 0 ? (
        <EmptyState title="No ingestion runs" />
      ) : null}
      <ul className="space-y-1">
        {data?.items.map((run) => (
          <li key={run.id} className="flex items-center justify-between text-xs text-slate-300">
            <span>
              {run.source_id} - {new Date(run.started_at).toLocaleString()}
            </span>
            <Badge variant={run.status === "success" ? "success" : "outline"}>{run.status}</Badge>
          </li>
        ))}
      </ul>
    </div>
  );
}

function AuditLogsTable() {
  const { data, isLoading, isError, error, refetch } = useAdminAuditLogs();

  if (isLoading) return <LoadingState label="Loading audit logs…" />;
  if (isError) {
    return (
      <ErrorState
        title="Failed to load audit logs"
        description={error instanceof Error ? error.message : undefined}
        onRetry={() => refetch()}
      />
    );
  }
  if (!data || data.items.length === 0) return <EmptyState title="No audit log entries" />;

  return (
    <ul className="space-y-1">
      {data.items.map((entry) => (
        <li key={entry.id} className="text-xs text-slate-300">
          <span className="font-mono text-[10px] text-slate-500">
            {new Date(entry.occurred_at).toLocaleString()}
          </span>{" "}
          {entry.actor_user_id ?? "system"} {entry.action} {entry.resource_type}
          {entry.resource_id ? `:${entry.resource_id}` : ""}
        </li>
      ))}
    </ul>
  );
}
