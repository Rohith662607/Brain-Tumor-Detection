"use client";

import { useState } from "react";
import { DetectionBox } from "@/lib/api";
import { cn } from "@/lib/utils";

interface ImageViewerProps {
  src: string;
  detections: DetectionBox[];
  analyzing?: boolean;
  emptyLabel?: string;
}

export function ImageViewer({ src, detections, analyzing = false, emptyLabel }: ImageViewerProps) {
  // Natural size is read from the loaded image itself (not passed in) so the
  // overlay math is always correct against whatever file was uploaded.
  const [natural, setNatural] = useState<{ w: number; h: number } | null>(null);
  const aspect = natural ? natural.w / natural.h : 1;
  const imageWidth = natural?.w ?? 1;
  const imageHeight = natural?.h ?? 1;

  return (
    <div className="relative w-full max-w-xl mx-auto">
      <div
        className="relative w-full overflow-hidden rounded-md bg-black"
        style={{ aspectRatio: aspect }}
      >
        {src ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={src}
            alt="MRI slice"
            className="h-full w-full object-contain"
            onLoad={(e) => {
              const el = e.currentTarget;
              setNatural({ w: el.naturalWidth, h: el.naturalHeight });
            }}
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-ink-faint font-mono text-xs">
            {emptyLabel ?? "no image loaded"}
          </div>
        )}

        {/* Detection overlays — positioned as % of image, so they track
            correctly regardless of the rendered element's actual pixel size */}
        {natural && detections.map((d, i) => {
          const [x1, y1, x2, y2] = d.bbox_xyxy;
          const left = (x1 / imageWidth) * 100;
          const top = (y1 / imageHeight) * 100;
          const w = ((x2 - x1) / imageWidth) * 100;
          const h = ((y2 - y1) / imageHeight) * 100;
          const positive = d.class_name === "positive";

          return (
            <div
              key={i}
              className={cn(
                "absolute animate-box-in border-2 rounded-sm",
                positive ? "border-signal-positive" : "border-cyan"
              )}
              style={{ left: `${left}%`, top: `${top}%`, width: `${w}%`, height: `${h}%` }}
            >
              <span
                className={cn(
                  "absolute -top-5 left-0 whitespace-nowrap rounded-sm px-1 py-0.5 text-[10px] font-mono leading-none",
                  positive ? "bg-signal-positive text-void" : "bg-cyan text-void"
                )}
              >
                {d.class_name} · {(d.confidence * 100).toFixed(0)}%
              </span>
            </div>
          );
        })}

        {/* scan sweep while a detection request is in flight */}
        {analyzing && (
          <div className="absolute inset-x-0 top-0 h-px animate-scan bg-gradient-to-r from-transparent via-cyan to-transparent shadow-[0_0_8px_1px_rgba(79,209,197,0.6)]" />
        )}

        {/* reticle corner brackets — signature framing element */}
        <div className="reticle-corner left-2 top-2 border-l-2 border-t-2" />
        <div className="reticle-corner right-2 top-2 border-r-2 border-t-2" />
        <div className="reticle-corner left-2 bottom-2 border-l-2 border-b-2" />
        <div className="reticle-corner right-2 bottom-2 border-r-2 border-b-2" />
      </div>
    </div>
  );
}
