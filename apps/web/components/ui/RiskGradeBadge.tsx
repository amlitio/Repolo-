import type { RiskGrade } from "@firip/shared";
import { gradeBadgeClass } from "@/lib/utils/risk";
import { cn } from "@/lib/utils/cn";

export function RiskGradeBadge({
  grade,
  score,
  className,
}: {
  grade: RiskGrade;
  score?: number;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-sm border px-2 py-0.5 font-mono text-xs font-bold",
        gradeBadgeClass(grade),
        className
      )}
    >
      <span>{grade}</span>
      {score !== undefined ? (
        <span className="font-normal opacity-80">{score.toFixed(1)}</span>
      ) : null}
    </span>
  );
}
