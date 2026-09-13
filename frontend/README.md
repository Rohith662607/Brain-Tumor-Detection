# Brain Tumor Detection — Frontend (Phase 3)

Next.js + Tailwind + hand-written shadcn-style primitives. Three views: New
scan (upload + live detection), History (past scans, delete, download
report), Model (what's currently serving).

**Verified in this sandbox:** `npm install`, `npx tsc --noEmit` (clean), and
a full `next build` all pass — every page compiles, types check, and all
routes prerender. The one thing that didn't run here is fetching the Google
Fonts at build time (`fonts.googleapis.com` isn't reachable from this
sandbox) — confirmed that's the *only* issue by temporarily stripping the
font import and re-running the build clean. On your machine, with normal
internet access, `next build` will fetch the fonts and just work. **Not
verified:** an actual live run against the backend (needs the backend
running with `torch`/`ultralytics` installed, which this sandbox couldn't
fit — same limitation as Phases 1–2).

## Design system

Not a marketing site — a radiology reading-room workspace. The palette (deep
navy-black, cyan for interactive/detection UI, red/green reserved *only* for
actual clinical verdicts) and the corner-bracket "reticle" viewer are meant
to echo how MRI slices actually get read, not a generic dark-mode template.
Space Grotesk for UI chrome, IBM Plex Sans for body text, IBM Plex Mono for
every number on screen (confidence, coordinates, area %) — so a reading feels
like an instrument readout, not prose.

## Setup

Requires the backend (Phase 2) running first.

```bash
cd frontend
npm install
cp .env.local.example .env.local   # point NEXT_PUBLIC_API_BASE_URL at your backend
npm run dev
```

Open http://localhost:3000.

## Structure

```
frontend/
├── app/
│   ├── page.tsx          # New scan: upload -> live detection -> findings
│   ├── history/page.tsx  # Past scans grid, delete, download report
│   └── model/page.tsx    # Currently-serving model info
├── components/
│   ├── image-viewer.tsx      # the reticle/bbox-overlay viewer (signature element)
│   ├── upload-dropzone.tsx
│   ├── findings-panel.tsx
│   ├── history-grid.tsx
│   ├── nav-rail.tsx
│   ├── verdict-badge.tsx
│   └── ui/                    # button, card, badge primitives
└── lib/
    ├── api.ts             # typed client — mirrors backend/app/schemas.py field-for-field
    └── utils.ts
```

## What's next (Phase 4, not in this drop)

Docker Compose tying `ml` + `backend` + `frontend` together, plus the
remaining docs (DEPLOYMENT_GUIDE.md, ARCHITECTURE.md, etc.).
