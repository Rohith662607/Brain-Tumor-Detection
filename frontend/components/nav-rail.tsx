"use client";

// REPLACES frontend/components/nav-rail.tsx (v4 — wider proper sidebar
// with a visible "ArbudaScan" name + subtitle header, horizontal
// icon+label nav rows, and a matching theme-toggle row at the bottom)

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ScanLine, History, Cpu, Bot, Sun, Moon } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTheme } from "@/lib/theme";

const items = [
  { href: "/", label: "New scan", icon: ScanLine },
  { href: "/history", label: "History", icon: History },
  { href: "/model", label: "Model", icon: Cpu },
  { href: "/assistant", label: "Assistant", icon: Bot },
];

export function NavRail() {
  const pathname = usePathname();
  const { theme, toggle } = useTheme();

  return (
    <nav className="relative z-10 flex w-60 shrink-0 flex-col border-r border-line bg-surface">
      <Link href="/" className="flex items-center gap-3 border-b border-line px-4 py-5">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-cyan/40 bg-cyan/10 text-cyan">
          <span className="font-display text-xs font-bold tracking-tight">AS</span>
        </div>
        <div className="min-w-0">
          <div className="font-display text-sm font-semibold leading-tight text-ink-primary">
            ArbudaScan
          </div>
          <div className="truncate text-[10px] leading-tight text-ink-faint">
            AI-Assisted Brain Tumor Detection &amp; Analysis
          </div>
        </div>
      </Link>

      <div className="flex flex-1 flex-col gap-1 px-3 py-4">
        {items.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              aria-current={active ? "page" : undefined}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors",
                active ? "bg-cyan/10 text-cyan" : "text-ink-muted hover:bg-raised hover:text-ink-primary"
              )}
            >
              <Icon size={17} strokeWidth={1.75} />
              {label}
            </Link>
          );
        })}
      </div>

      <div className="border-t border-line px-3 py-3">
        <button
          onClick={toggle}
          className="flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium text-ink-muted transition-colors hover:bg-raised hover:text-ink-primary"
        >
          {theme === "light" ? <Moon size={17} strokeWidth={1.75} /> : <Sun size={17} strokeWidth={1.75} />}
          {theme === "light" ? "Dark mode" : "Light mode"}
        </button>
      </div>
    </nav>
  );
}
