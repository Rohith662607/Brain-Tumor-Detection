"use client";

// REPLACES frontend/components/history-detail-modal.tsx (v3 — gap-4 ->
// gap-5 in the left column, matching the New scan page's spacing)

import { useEffect, useState } from "react";
import { api, DetectionDetail, ApiError } from "@/lib/api";
import { FindingsPanel } from "@/components/findings-panel";
import { AiReportPanel } from "@/components/ai-report-panel";
import { X, Loader2 } from "lucide-react";

export function HistoryDetailModal({ id, onClose }: { id: number; onClose: () => void }) {
  const [detail, setDetail] = useState<DetectionDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setDetail(null);
    setError(null);
    api
      .historyDetail(id)
      .then((d) => {
        if (!cancelled) setDetail(d);
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof ApiError ? e.message : "Couldn't load this scan.");
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink-primary/40 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="animate-box-in flex max-h-[90vh] w-full max-w-5xl flex-col overflow-hidden rounded-lg border border-line bg-void shadow-raised"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-line bg-surface px-5 py-3">
          <div>
            <h2 className="font-display text-sm font-semibold text-ink-primary">
              Scan {detail ? `#${detail.id}` : `#${id}`}
            </h2>
            {detail && <p className="font-mono text-[11px] text-ink-faint">{detail.original_filename}</p>}
          </div>
          <button
            onClick={onClose}
            aria-label="Close"
            className="flex h-8 w-8 items-center justify-center rounded-md text-ink-faint hover:bg-raised hover:text-ink-primary"
          >
            <X size={16} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-5">
          {error && <p className="text-sm text-signal-positive">{error}</p>}

          {!detail && !error && (
            <div className="flex items-center justify-center gap-2 py-16 text-sm text-ink-muted">
              <Loader2 size={16} className="animate-spin text-cyan" />
              Loading scan…
            </div>
          )}

          {detail && (
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1.3fr_1fr]">
              <div className="flex flex-col gap-5">
                <div className="overflow-hidden rounded-md border border-line bg-black">
                  {detail.annotated_image_url && (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={api.imageUrl(detail.annotated_image_url)}
                      alt={detail.original_filename}
                      className="w-full object-contain"
                    />
                  )}
                </div>
                <AiReportPanel detectionId={detail.id} initialReport={detail.ai_report} />
              </div>
              <FindingsPanel result={detail} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
