"use client";

// REPLACES frontend/components/history-grid.tsx (v2 — clickable cards
// open the detail modal, plus a visible Scan ID badge)

import { DetectionSummary, api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Trash2, FileDown } from "lucide-react";

export function HistoryGrid({
  items,
  onDelete,
  onOpen,
}: {
  items: DetectionSummary[];
  onDelete: (id: number) => void;
  onOpen: (id: number) => void;
}) {
  if (items.length === 0) {
    return (
      <div className="rounded-md border border-dashed border-line p-10 text-center font-mono text-xs text-ink-faint">
        No scans yet. Run a detection from "New scan" to see it here.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
      {items.map((item) => (
        <div
          key={item.id}
          role="button"
          tabIndex={0}
          onClick={() => onOpen(item.id)}
          onKeyDown={(e) => e.key === "Enter" && onOpen(item.id)}
          className="group relative cursor-pointer overflow-hidden rounded-md border border-line bg-surface transition-shadow hover:shadow-raised"
        >
          <div className="aspect-square bg-black">
            {item.annotated_image_url && (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={api.imageUrl(item.annotated_image_url)}
                alt={item.original_filename}
                className="h-full w-full object-cover"
              />
            )}
          </div>
          <div className="p-2">
            <div className="flex items-center justify-between">
              <Badge tone={item.tumor_detected ? "positive" : "clear"}>
                {item.tumor_detected ? "tumor" : "clear"}
              </Badge>
              <span className="font-mono text-[10px] text-ink-faint">
                {new Date(item.created_at).toLocaleDateString()}
              </span>
            </div>
            <p className="mt-1 truncate font-mono text-[11px] text-ink-muted" title={item.original_filename}>
              {item.original_filename}
            </p>
          </div>

          <div className="absolute left-2 top-2 rounded bg-void/85 px-1.5 py-0.5 font-mono text-[10px] text-ink-primary shadow-sm">
            #{item.id}
          </div>

          <div className="absolute right-2 top-2 hidden gap-1 group-hover:flex">
            {item.pdf_report_url && (
              <a
                href={api.reportUrl(item.pdf_report_url)}
                target="_blank"
                rel="noreferrer"
                onClick={(e) => e.stopPropagation()}
              >
                <Button size="sm" variant="outline" className="!h-7 !px-2">
                  <FileDown size={12} />
                </Button>
              </a>
            )}
            <Button
              size="sm"
              variant="danger"
              className="!h-7 !px-2"
              onClick={(e) => {
                e.stopPropagation();
                onDelete(item.id);
              }}
            >
              <Trash2 size={12} />
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
}
