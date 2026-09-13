import type { Config } from "tailwindcss";

// Design tokens now resolve through CSS variables (defined in globals.css
// for :root = light and html.dark = dark), using the
// `rgb(var(--x) / <alpha-value>)` pattern so Tailwind's opacity utilities
// (bg-cyan/10, text-signal-positive/40, etc.) still work correctly.
// Every component still just uses the same semantic class names as
// before — bg-surface, text-ink-primary, etc. — so NONE of them needed
// to change for theming to work.
const config: Config = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        void: "rgb(var(--color-void) / <alpha-value>)",
        surface: "rgb(var(--color-surface) / <alpha-value>)",
        raised: "rgb(var(--color-raised) / <alpha-value>)",
        line: "rgb(var(--color-line) / <alpha-value>)",
        ink: {
          primary: "rgb(var(--color-ink-primary) / <alpha-value>)",
          muted: "rgb(var(--color-ink-muted) / <alpha-value>)",
          faint: "rgb(var(--color-ink-faint) / <alpha-value>)",
        },
        cyan: {
          DEFAULT: "rgb(var(--color-cyan) / <alpha-value>)",
          dim: "rgb(var(--color-cyan-dim) / <alpha-value>)",
        },
        signal: {
          positive: "rgb(var(--color-signal-positive) / <alpha-value>)",
          "positive-dim": "rgb(var(--color-signal-positive-dim) / <alpha-value>)",
          clear: "rgb(var(--color-signal-clear) / <alpha-value>)",
          "clear-dim": "rgb(var(--color-signal-clear-dim) / <alpha-value>)",
        },
        "accent-ink": "rgb(var(--color-accent-ink) / <alpha-value>)",
      },
      fontFamily: {
        display: ["var(--font-display)", "system-ui", "sans-serif"],
        body: ["var(--font-body)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      borderRadius: {
        sm: "6px",
        DEFAULT: "10px",
        md: "12px",
        lg: "16px",
      },
      boxShadow: {
        card: "0 1px 2px 0 rgb(0 0 0 / 0.04), 0 1px 8px -2px rgb(0 0 0 / 0.08)",
        raised: "0 4px 16px -4px rgb(0 0 0 / 0.16)",
      },
      keyframes: {
        scan: {
          "0%": { transform: "translateY(0%)", opacity: "0" },
          "10%": { opacity: "1" },
          "90%": { opacity: "1" },
          "100%": { transform: "translateY(100%)", opacity: "0" },
        },
        "fade-in": { from: { opacity: "0" }, to: { opacity: "1" } },
        "box-in": {
          from: { opacity: "0", transform: "scale(1.04)" },
          to: { opacity: "1", transform: "scale(1)" },
        },
        "slide-up": {
          from: { opacity: "0", transform: "translateY(6px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "node-pulse": {
          "0%, 100%": { opacity: "0.35", transform: "scale(1)" },
          "50%": { opacity: "0.9", transform: "scale(1.35)" },
        },
        "line-glow": {
          "0%, 100%": { opacity: "0.12" },
          "50%": { opacity: "0.35" },
        },
      },
      animation: {
        scan: "scan 1.8s ease-in-out infinite",
        "fade-in": "fade-in 0.3s ease-out",
        "box-in": "box-in 0.25s ease-out",
        "slide-up": "slide-up 0.2s ease-out",
        "node-pulse": "node-pulse 4s ease-in-out infinite",
        "line-glow": "line-glow 6s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
