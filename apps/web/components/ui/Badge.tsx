import { cva, type VariantProps } from "class-variance-authority";
import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils/cn";

export const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-sm border px-1.5 py-0.5 text-[10px] font-mono font-medium uppercase tracking-wider",
  {
    variants: {
      variant: {
        default: "border-slate-700 bg-slate-800 text-slate-200",
        outline: "border-slate-600 bg-transparent text-slate-300",
        success: "border-emerald-500/40 bg-emerald-500/15 text-emerald-400",
        warning: "border-yellow-500/40 bg-yellow-500/15 text-yellow-400",
        danger: "border-red-500/40 bg-red-500/15 text-red-400",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}
