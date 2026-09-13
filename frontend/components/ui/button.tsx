// REPLACES frontend/components/ui/button.tsx (v3 — accent-ink token for
// theme-correct contrast on the primary button, instead of hardcoded white)

import { ButtonHTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/utils";

type Variant = "primary" | "ghost" | "outline" | "danger";
type Size = "sm" | "md";

const variantClasses: Record<Variant, string> = {
  primary: "bg-cyan text-accent-ink hover:bg-cyan/90 font-medium shadow-sm",
  ghost: "bg-transparent text-ink-muted hover:text-ink-primary hover:bg-raised",
  outline: "border border-line text-ink-primary hover:border-cyan/50 hover:bg-raised bg-transparent",
  danger: "bg-transparent text-signal-positive hover:bg-signal-positive-dim border border-signal-positive/30",
};

const sizeClasses: Record<Size, string> = {
  sm: "h-8 px-3 text-xs",
  md: "h-10 px-4 text-sm",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-md transition-colors duration-150 disabled:opacity-40 disabled:cursor-not-allowed",
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
      {...props}
    />
  )
);
Button.displayName = "Button";
