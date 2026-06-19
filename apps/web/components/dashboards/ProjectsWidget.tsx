"use client";

import { useProjects } from "@/lib/hooks/useProjects";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/States";

export function ProjectsWidget() {
  const { data, isLoading, isError, error, refetch } = useProjects();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Projects</CardTitle>
        {data ? <Badge variant="outline">{data.total}</Badge> : null}
      </CardHeader>
      <CardContent>
        {isLoading ? <LoadingState label="Loading projects…" /> : null}
        {isError ? (
          <ErrorState
            title="Failed to load projects"
            description={error instanceof Error ? error.message : undefined}
            onRetry={() => refetch()}
          />
        ) : null}
        {!isLoading && !isError && data?.items.length === 0 ? (
          <EmptyState title="No projects yet" />
        ) : null}
        <ul className="space-y-1.5">
          {data?.items.slice(0, 6).map((project) => (
            <li key={project.id} className="flex items-center justify-between text-xs text-slate-300">
              <span className="truncate">{project.name}</span>
              {project.status ? <Badge variant="outline">{project.status}</Badge> : null}
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
