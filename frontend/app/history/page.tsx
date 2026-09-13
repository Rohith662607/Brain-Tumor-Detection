"use client";

// REPLACES frontend/app/history/page.tsx (v2 — wires up the detail modal)

import { useEffect, useState } from "react";
import { api, DetectionSummary } from "@/lib/api";
import { HistoryGrid } from "@/components/history-grid";
import { HistoryDetailModal } from "@/components/history-detail-modal";

export default function HistoryPage() {
  const [items, setItems] = useState<DetectionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [openId, setOpenId] = useState<number | null>(null);

  async function load() {
    setLoading(true);
    try {
      const page = await api.history(60, 0);
      setItems(page.items);
      setError(null);
    } catch {
      setError("Couldn't reach the detection service.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleDelete(id: number) {
    setItems((prev) => prev.filter((i) => i.id !== id));
    try {
      await api.deleteDetection(id);
    } catch {
      load(); // reconcile if the delete failed server-side
    }
  }

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6 p-6">
      <header>
        <h1 className="font-display text-lg font-semibold tracking-tight">History</h1>
        <p className="font-mono text-xs text-ink-faint">{items.length} scan(s) on record</p>
      </header>

      {loading && <p className="font-mono text-xs text-ink-faint">Loading…</p>}
      {error && <p className="font-mono text-xs text-signal-positive">{error}</p>}
      {!loading && !error && <HistoryGrid items={items} onDelete={handleDelete} onOpen={setOpenId} />}

      {openId !== null && <HistoryDetailModal id={openId} onClose={() => setOpenId(null)} />}
    </div>
  );
}
