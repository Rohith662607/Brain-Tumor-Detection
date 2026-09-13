import { cn } from "@/lib/utils";

export function VerdictBadge({ tumorDetected }: { tumorDetected: boolean }) {
  return (
    <div
      className={cn(
        "flex items-center gap-2 rounded-md border px-3 py-2 font-display text-sm font-semibold tracking-wide",
        tumorDetected
          ? "border-signal-positive/40 bg-signal-positive-dim text-signal-positive"
          : "border-signal-clear/40 bg-signal-clear-dim text-signal-clear"
      )}
    >
      <span
        className={cn(
          "h-2 w-2 rounded-full",
          tumorDetected ? "bg-signal-positive" : "bg-signal-clear"
        )}
        aria-hidden
      />
      {tumorDetected ? "TUMOR DETECTED" : "NO TUMOR DETECTED"}
    </div>
  );
}
