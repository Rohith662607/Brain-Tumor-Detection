// REPLACES frontend/components/findings-panel.tsx (v8 — gap-4 -> gap-5,
// matching the left column's spacing for a consistent look)

import { DetectionDetail, api } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { VerdictBadge } from "@/components/verdict-badge";
import { ChatPanel } from "@/components/chat-panel";
import { Download } from "lucide-react";

export function FindingsPanel({ result }: { result: DetectionDetail }) {
  return (
    <div className="flex flex-col gap-5">
      <VerdictBadge tumorDetected={result.tumor_detected} />

      <Card>
        <CardHeader>
          <CardTitle>Summary</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-2 gap-3 font-mono text-sm">
          <Metric label="scan id" value={`#${result.id}`} />
          <Metric label="detections" value={String(result.num_detections)} />
          <Metric label="tumor area" value={`${result.total_tumor_area_pct.toFixed(2)}%`} />
          <Metric
            label="scanned"
            value={new Date(result.created_at).toLocaleString()}
            mono={false}
          />
          <Metric label="file" value={result.original_filename} mono={false} span />
        </CardContent>
      </Card>

      <ChatPanel detectionId={result.id} />

      <Card>
        <CardHeader>
          <CardTitle>Detections ({result.detections.length})</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-2 p-2">
          {result.detections.length === 0 && (
            <p className="px-2 py-3 text-sm text-ink-muted">
              No regions of interest found above the confidence threshold.
            </p>
          )}
          {result.detections.map((d, i) => (
            <div
              key={i}
              className="rounded-md border border-line bg-raised px-3 py-2 text-xs font-mono"
            >
              <div className="flex items-center justify-between">
                <span
                  className={d.class_name === "positive" ? "text-signal-positive" : "text-cyan"}
                >
                  {d.class_name}
                </span>
                <span className="text-ink-muted">{(d.confidence * 100).toFixed(1)}% conf</span>
              </div>
              <div className="mt-1 flex items-center justify-between text-ink-faint">
                <span>
                  bbox [{d.bbox_xyxy.map((v) => v.toFixed(0)).join(", ")}]
                </span>
                <span>{d.area_pct_of_image?.toFixed(2)}% area</span>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {result.pdf_report_url && (
        <a href={api.reportUrl(result.pdf_report_url)} target="_blank" rel="noreferrer">
          <Button variant="outline" className="w-full">
            <Download size={14} /> Download PDF report
          </Button>
        </a>
      )}
    </div>
  );
}

function Metric({
  label,
  value,
  mono = true,
  span = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
  span?: boolean;
}) {
  return (
    <div className={span ? "col-span-2" : undefined}>
      <div className="text-[10px] uppercase tracking-wider text-ink-faint">{label}</div>
      <div className={mono ? "font-mono text-ink-primary" : "font-body text-ink-primary truncate"}>
        {value}
      </div>
    </div>
  );
}
