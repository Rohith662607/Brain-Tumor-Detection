"use client";

// NEW FILE — save as frontend/components/theme-toggle.tsx

import { Sun, Moon } from "lucide-react";
import { useTheme } from "@/lib/theme";

export function ThemeToggle() {
  const { theme, toggle } = useTheme();
  return (
    <button
      onClick={toggle}
      title={theme === "light" ? "Switch to dark theme" : "Switch to light theme"}
      aria-label="Toggle color theme"
      className="flex h-10 w-10 items-center justify-center rounded-md text-ink-faint transition-colors hover:bg-raised hover:text-ink-primary"
    >
      {theme === "light" ? <Moon size={17} strokeWidth={1.75} /> : <Sun size={17} strokeWidth={1.75} />}
    </button>
  );
}
