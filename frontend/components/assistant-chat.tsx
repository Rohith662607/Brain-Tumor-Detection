"use client";

// NEW FILE — save as frontend/components/assistant-chat.tsx
//
// The global Assistant — separate from the per-scan chat. Knows about the
// app itself and can answer questions about any past scan by ID or
// filename (the backend looks up matching history records and grounds the
// answer in that data). Conversation is kept in memory for this session
// only (not persisted across a page reload) — the backend is stateless
// and receives the full running history on each request.

import { useEffect, useRef, useState } from "react";
import { api, ApiError, ChatMessage } from "@/lib/api";
import { Loader2, Send, Bot } from "lucide-react";
import { cn } from "@/lib/utils";

const SUGGESTIONS = [
  "What does ArbudaScan do?",
  "How many scans are in history?",
  "Tell me about scan #1",
];

export function AssistantChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  async function send(text: string) {
    const trimmed = text.trim();
    if (!trimmed || sending) return;

    setInput("");
    setError(null);
    const optimistic = [...messages, { role: "user" as const, content: trimmed }];
    setMessages(optimistic);
    setSending(true);

    try {
      const res = await api.assistantChat(trimmed, messages);
      setMessages(res.history);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't reach the assistant.");
      setMessages(messages);
      setInput(trimmed);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="flex h-full flex-col gap-4">
      <div className="flex flex-1 flex-col gap-3 overflow-y-auto rounded-lg border border-line bg-surface p-4 shadow-card">
        {messages.length === 0 && !sending && (
          <div className="flex flex-1 flex-col items-center justify-center gap-4 py-10 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-cyan/10 text-cyan">
              <Bot size={22} />
            </div>
            <div>
              <p className="text-sm font-medium text-ink-primary">Ask the Assistant</p>
              <p className="mt-1 text-xs text-ink-muted">
                Ask about how ArbudaScan works, or about any scan in your history by ID or filename.
              </p>
            </div>
            <div className="flex flex-col gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="rounded-md border border-line bg-raised px-3 py-1.5 text-xs text-ink-muted transition-colors hover:border-cyan/50 hover:text-ink-primary"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div
            key={i}
            className={cn(
              "animate-slide-up max-w-[85%] whitespace-pre-wrap rounded-md px-3 py-2 text-sm leading-relaxed",
              m.role === "user" ? "self-end bg-cyan text-accent-ink" : "self-start bg-raised text-ink-primary"
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
              send(input);
            }
          }}
          placeholder="Ask about ArbudaScan or a past scan…"
          disabled={sending}
          className="flex-1 rounded-md border border-line bg-void px-3 py-2.5 text-sm text-ink-primary placeholder:text-ink-faint focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan disabled:opacity-50"
        />
        <button
          onClick={() => send(input)}
          disabled={sending || !input.trim()}
          className="flex h-[42px] w-[42px] items-center justify-center rounded-md bg-cyan text-accent-ink transition-colors hover:bg-cyan/90 disabled:opacity-40"
        >
          <Send size={15} />
        </button>
      </div>
    </div>
  );
}
