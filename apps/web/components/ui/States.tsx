import type { ReactNode } from "react";
import { cn } from "@/lib/utils/cn";

export function Spinner({ className }: { className?: string }) {
  return (
    <div
      role="status"
      aria-label="Loading"
      className={cn(
        "h-4 w-4 animate-spin rounded-full border-2 border-slate-700 border-t-cyan-400",
        className
      )}
    />
  );
}

export function LoadingState({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 px-3 py-6 text-xs text-slate-400">
      <Spinner />
      <span>{label}</span>
    </div>
  );
}

export function EmptyState({
  title = "No data",
  description,
  icon,
}: {
  title?: string;
  description?: string;
  icon?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center gap-1 px-3 py-8 text-center text-slate-500">
      {icon}
      <p className="text-xs font-medium text-slate-400">{title}</p>
      {description ? <p className="text-[11px] text-slate-500">{description}</p> : null}
    </div>
  );
}

export function ErrorState({
  title = "Something went wrong",
  description,
  onRetry,
}: {
  title?: string;
  description?: string;
  onRetry?: () => void;
}) {
  return (
    <div className="flex flex-col items-center gap-2 px-3 py-8 text-center">
      <p className="text-xs font-medium text-red-400">{title}</p>
      {description ? <p className="text-[11px] text-slate-500">{description}</p> : null}
      {onRetry ? (
        <button
          onClick={onRetry}
          className="mt-1 rounded-sm border border-slate-700 px-2 py-1 text-[11px] text-slate-300 hover:bg-slate-800"
        >
          Retry
        </button>
      ) : null}
    </div>
  );
}
