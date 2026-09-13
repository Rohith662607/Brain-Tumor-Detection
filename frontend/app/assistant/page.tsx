// NEW FILE — save as frontend/app/assistant/page.tsx

import { AssistantChat } from "@/components/assistant-chat";

export default function AssistantPage() {
  return (
    <div className="mx-auto flex h-full max-w-3xl flex-col gap-6 p-6">
      <header>
        <h1 className="font-display text-lg font-semibold tracking-tight">Assistant</h1>
        <p className="font-mono text-xs text-ink-faint">
          Ask about ArbudaScan itself, or any past scan by ID or filename
        </p>
      </header>
      <div className="flex-1 overflow-hidden">
        <AssistantChat />
      </div>
    </div>
  );
}
