"use client";

import { useEffect, useState } from "react";
import { api, ModelInfo, HealthStatus } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function ModelPage() {
  const [info, setInfo] = useState<ModelInfo | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.modelInfo(), api.health()])
      .then(([i, h]) => {
        setInfo(i);
        setHealth(h);
      })
      .catch(() => setError("Couldn't reach the detection service."));
  }, []);

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6 p-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-lg font-semibold tracking-tight">Model</h1>
          <p className="font-mono text-xs text-ink-faint">what's currently serving detections</p>
        </div>
        {health && (
          <Badge tone={health.model_loaded ? "clear" : "positive"}>
            {health.model_loaded ? "loaded" : "not loaded"}
          </Badge>
        )}
      </header>

      {error && <p className="font-mono text-xs text-signal-positive">{error}</p>}

      {info && (
        <Card>
          <CardHeader>
            <CardTitle>Configuration</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-4 font-mono text-sm">
            <Field label="weights" value={info.weights_path} span />
            <Field label="classes" value={info.class_names.join(", ")} span />
            <Field label="input size" value={`${info.image_size}px`} />
            <Field label="device" value={info.device} />
            <Field label="confidence threshold" value={String(info.conf_threshold)} />
            <Field label="IoU threshold" value={String(info.iou_threshold)} />
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function Field({ label, value, span = false }: { label: string; value: string; span?: boolean }) {
  return (
    <div className={span ? "col-span-2" : undefined}>
      <div className="text-[10px] uppercase tracking-wider text-ink-faint">{label}</div>
      <div className="truncate text-ink-primary">{value}</div>
    </div>
  );
}
