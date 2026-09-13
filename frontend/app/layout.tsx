// REPLACES frontend/app/layout.tsx (v3 — ArbudaScan branding, theme
// provider + no-flash boot script, animated neuron background)

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
            <main className="flex-1 overflow-y-auto">{children}</main>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
