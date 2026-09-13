// REPLACES frontend/app/layout.tsx (v2 — main content padded on mobile so
// it isn't hidden behind the new fixed top/bottom mobile nav bars; the
// desktop/tablet layout is unaffected since that padding is sm:0)

import type { Metadata } from "next";
import { Space_Grotesk, IBM_Plex_Sans, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";
import { NavRail } from "@/components/nav-rail";
import { NeuronBackground } from "@/components/neuron-background";
import { ThemeProvider, noFlashThemeScript } from "@/lib/theme";

const display = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["500", "600", "700"],
});

const body = IBM_Plex_Sans({
  subsets: ["latin"],
  variable: "--font-body",
  weight: ["400", "500", "600"],
});

const mono = IBM_Plex_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: "ArbudaScan — AI-Assisted Brain Tumor Detection & Analysis",
  description: "Upload an MRI slice and get tumor location, confidence, and area in seconds.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${display.variable} ${body.variable} ${mono.variable}`}>
      <head>
        <script dangerouslySetInnerHTML={{ __html: noFlashThemeScript }} />
      </head>
      <body>
        <ThemeProvider>
          <NeuronBackground />
          <div className="relative z-10 flex h-screen w-screen overflow-hidden">
            <NavRail />
            <main className="flex-1 overflow-y-auto pt-14 pb-16 sm:pt-0 sm:pb-0">{children}</main>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
