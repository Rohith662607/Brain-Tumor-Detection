"use client";

// REPLACES frontend/app/page.tsx (v3 — gap-4 -> gap-5 for more consistent
// breathing room between the image, AI report, and the right-hand column)

import { useState } from "react";
import { UploadDropzone } from "@/components/upload-dropzone";
import { ImageViewer } from "@/components/image-viewer";
import { FindingsPanel } from "@/components/findings-panel";
import { AiReportPanel } from "@/components/ai-report-panel";
import { Button } from "@/components/ui/button";
import { api, ApiError, DetectionDetail } from "@/lib/api";
import { RotateCcw } from "lucide-react";

type Status = "idle" | "analyzing" | "done" | "error";

export default function NewScanPage() {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [status, setStatus] = useState<Status>("idle");
  const [result, setResult] = useState<DetectionDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleFile(file: File) {
    setPreviewUrl(URL.createObjectURL(file));
    setResult(null);
    setError(null);
    setStatus("analyzing");
    try {
      const detection = await api.detect(file);
      setResult(detection);
      setStatus("done");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't reach the detection service.");
      setStatus("error");
    }
  }

  function reset() {
    setPreviewUrl(null);
    setResult(null);
    setError(null);
    setStatus("idle");
  }

  return (
    <div className="mx-auto flex h-full max-w-6xl flex-col gap-6 p-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-lg font-semibold tracking-tight">New scan</h1>
          <p className="font-mono text-xs text-ink-faint">
            axial · coronal · sagittal T1WCE MRI supported
          </p>
        </div>
        {status !== "idle" && (
          <Button variant="ghost" size="sm" onClick={reset}>
            <RotateCcw size={14} /> New upload
          </Button>
        )}
      </header>

      {status === "idle" && (
        <div className="flex flex-1 items-center justify-center">
          <div className="w-full max-w-md">
            <UploadDropzone onFileSelected={handleFile} />
          </div>
        </div>
      )}

      {status !== "idle" && previewUrl && (
        <div className="grid flex-1 grid-cols-1 gap-6 lg:grid-cols-[1fr_320px]">
          <div className="flex flex-col gap-5">
            <ImageViewer
              src={previewUrl}
              detections={result?.detections ?? []}
              analyzing={status === "analyzing"}
            />
            {status === "analyzing" && (
              <p className="text-center font-mono text-xs text-cyan animate-fade-in">
                analyzing slice…
              </p>
            )}
            {status === "error" && (
              <p className="text-center font-mono text-xs text-signal-positive">{error}</p>
            )}
            {status === "done" && result && (
              <AiReportPanel detectionId={result.id} initialReport={result.ai_report} />
            )}
          </div>

          <div>
            {status === "done" && result ? (
              <FindingsPanel result={result} />
            ) : (
              <div className="rounded-md border border-line bg-surface p-4 font-mono text-xs text-ink-faint">
                {status === "analyzing" ? "Running inference…" : "Findings will appear here."}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
