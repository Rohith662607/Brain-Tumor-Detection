"use client";

// REPLACES frontend/components/chat-panel.tsx (v2 — accent-ink token
// instead of hardcoded text-white, for correct contrast in both themes)

import { useEffect, useRef, useState } from "react";
import { api, ApiError, ChatMessage } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { MessageCircle, Loader2, Send } from "lucide-react";
import { cn } from "@/lib/utils";

export function ChatPanel({ detectionId }: { detectionId: number }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    setLoadingHistory(true);
    api
      .getChat(detectionId)
      .then((res) => {
        if (!cancelled) setMessages(res.history);
      })
      .catch(() => {
        // no existing chat yet is fine — just start with an empty thread
      })
      .finally(() => {
        if (!cancelled) setLoadingHistory(false);
      });
    return () => {
      cancelled = true;
    };
  }, [detectionId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  async function handleSend() {
    const text = input.trim();
    if (!text || sending) return;

    setInput("");
    setError(null);
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setSending(true);

    try {
      const res = await api.sendChatMessage(detectionId, text);
      setMessages(res.history);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't reach the chat service.");
      setMessages((prev) => prev.slice(0, -1));
      setInput(text);
    } finally {
      setSending(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MessageCircle size={14} className="text-cyan" />
          Ask about this scan
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <div className="flex max-h-72 flex-col gap-2 overflow-y-auto">
          {loadingHistory && (
            <div className="flex items-center gap-2 py-1 text-sm text-ink-muted">
              <Loader2 size={13} className="animate-spin" />
              Loading conversation…
            </div>
          )}

          {!loadingHistory && messages.length === 0 && (
            <p className="text-sm text-ink-muted">
              Ask a question about this scan's detection results — e.g. "how confident is
              this?" or "where exactly is the region?"
            </p>
          )}

          {messages.map((m, i) => (
            <div
              key={i}
              className={cn(
                "animate-slide-up max-w-[88%] rounded-md px-3 py-2 text-sm leading-relaxed",
                m.role === "user"
                  ? "self-end bg-cyan text-accent-ink"
                  : "self-start bg-raised text-ink-primary"
              )}
            >
              {m.content}
            </div>
          ))}

          {sending && (
            <div className="flex items-center gap-2 self-start rounded-md bg-raised px-3 py-2 text-sm text-ink-muted">
              <Loader2 size={13} className="animate-spin text-cyan" />
              Thinking…
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {error && <p className="text-xs text-signal-positive">{error}</p>}

        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Ask a question about this scan…"
            disabled={sending}
            className="flex-1 rounded-md border border-line bg-void px-3 py-2 text-sm text-ink-primary placeholder:text-ink-faint focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan disabled:opacity-50"
          />
          <Button size="sm" onClick={handleSend} disabled={sending || !input.trim()}>
            <Send size={13} />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
