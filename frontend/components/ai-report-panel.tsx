"use client";

// NEW FILE — save as frontend/components/ai-report-panel.tsx
//
// Replaces the old always-on "AI Report" card. Now the report only
// generates when the user clicks the button, showing a loading state
// while GitHub Models responds, and an inline retry on failure.

import { useState } from "react";
import { api, ApiError } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Sparkles, Loader2, RefreshCw } from "lucide-react";

export function AiReportPanel({
  detectionId,
  initialReport,
}: {
  detectionId: number;
  initialReport: string | null;
}) {
  const [report, setReport] = useState<string | null>(initialReport);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const detail = await api.generateReport(detectionId);
      setReport(detail.ai_report);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't reach the AI report service.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <Sparkles size={14} className="text-cyan" />
          AI Report
        </CardTitle>
        {report && !loading && (
          <Button variant="ghost" size="sm" onClick={handleGenerate} aria-label="Regenerate report">
            <RefreshCw size={13} />
          </Button>
        )}
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {report && (
          <p className="animate-fade-in whitespace-pre-wrap text-sm leading-relaxed text-ink-primary">
            {report}
          </p>
        )}

        {!report && !loading && (
          <div className="flex flex-col items-start gap-3">
            <p className="text-sm text-ink-muted">
              Generate a plain-language summary of this scan's findings using AI.
            </p>
            <Button size="sm" onClick={handleGenerate}>
              <Sparkles size={13} /> Generate report
            </Button>
          </div>
        )}

        {loading && (
          <div className="flex items-center gap-2 py-1 text-sm text-ink-muted">
            <Loader2 size={14} className="animate-spin text-cyan" />
            Analyzing findings…
          </div>
        )}

        {error && (
          <div className="flex flex-col items-start gap-2 rounded-md border border-signal-positive/30 bg-signal-positive-dim px-3 py-2">
            <p className="text-xs text-signal-positive">{error}</p>
            <Button size="sm" variant="outline" onClick={handleGenerate}>
              <RefreshCw size={13} /> Try again
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
