import { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type Tone = "neutral" | "positive" | "clear" | "cyan";

const toneClasses: Record<Tone, string> = {
  neutral: "bg-raised text-ink-muted border-line",
  positive: "bg-signal-positive-dim text-signal-positive border-signal-positive/30",
  clear: "bg-signal-clear-dim text-signal-clear border-signal-clear/30",
  cyan: "bg-cyan/10 text-cyan border-cyan/30",
};

export function Badge({
  className,
  tone = "neutral",
  ...props
}: HTMLAttributes<HTMLSpanElement> & { tone?: Tone }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded border px-2 py-0.5 text-xs font-mono",
        toneClasses[tone],
        className
      )}
      {...props}
    />
  );
}
