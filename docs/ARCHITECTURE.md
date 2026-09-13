# ARCHITECTURE.md

## Overview

```
┌─────────────┐      HTTP/JSON       ┌──────────────┐      imports        ┌─────────────┐
│  frontend/  │  ───────────────────▶│  backend/    │ ───────────────────▶│  ml/        │
│  Next.js    │◀─────────────────────│  FastAPI     │◀─────────────────────│  predict.py │
│  (browser)  │   JSON + image/PDF   │  (1 process) │   summary dict       │  train.py   │
└─────────────┘                      └──────┬───────┘                     └─────────────┘
                                             │
                                    ┌────────┴────────┐
                                    │  SQLite / storage│
                                    │  (detections db, │
                                    │  uploads, reports)│
                                    └───────────────────┘
```

Three independently runnable pieces, each with its own README:
- **`ml/`** (Phase 1) — dataset prep, training, evaluation, inference, export.
  Pure Python + PyTorch/Ultralytics, no web framework. Can be used entirely
  on its own from the CLI (e.g. on a Colab GPU) with no backend running.
- **`backend/`** (Phase 2) — FastAPI service. Imports `ml/predict.py`'s
  functions directly (not over HTTP, not as a subprocess) — the model is
  loaded once into the same process's memory at startup and reused across
  requests. Owns persistence (SQLite) and file storage (uploads/annotated
  images/reports).
- **`frontend/`** (Phase 3) — Next.js app. Talks to the backend only over
  its public HTTP API (`lib/api.ts`); has no knowledge of `ml/` or model
  internals.

## Why this split (and not, e.g., a monolith or a separate inference microservice)

- **`ml/` importable, not networked, from `backend/`**: an HTTP hop between
  backend and model adds latency and a second process to keep alive for no
  benefit at this scale (single model, single machine deployment target).
  If you later need to scale inference independently of the API (e.g. a GPU
  worker pool), `inference_service.py` is the one file that would change —
  everything else is unaffected because routers only ever call into it, never
  into `ultralytics` directly.
- **Single loaded model per backend process** (`--workers 1` in the
  Dockerfile): loading a YOLO checkpoint takes real time and VRAM/RAM; the
  original project's `gui.py` mistake (reloading/mismatching models) is the
  cautionary tale here. Scale by running more backend containers behind a
  load balancer, not more workers inside one.
- **SQLite by default**: this is a single-writer, low-concurrency workload
  (one clinician uploading one scan at a time, roughly). SQLite is zero-config
  and the WAL mode FastAPI+SQLModel use here handles that fine. `db.py`
  isolates all storage access behind `get_session()`/helper functions, so
  swapping `APP_DATABASE_URL` for Postgres is a config change, not a rewrite.
- **Local filesystem storage**: same reasoning — no S3/cloud dependency for
  a single-instance deployment. `config.py`'s `storage_dir` is the one place
  that would change to point at a mounted volume or (per `API_SETUP_GUIDE.md`)
  MinIO later.

## Request flow: uploading a scan

1. Frontend `UploadDropzone` gets a File, `NewScanPage` immediately shows a
   local object-URL preview (no round trip needed to see the image).
2. `api.detect(file)` POSTs multipart form data to `POST /api/detect`.
3. `routers/detect.py`: validates content-type/size, writes the upload to
   `storage/uploads/<uuid>.jpg`, calls `inference_service.predict()`.
4. `inference_service.py` calls `ml/predict.py`'s `run_inference()` against
   the already-loaded model — returns a structured summary (boxes, confidence,
   area %).
5. `detect.py` annotates the image, writes JSON + PDF reports, persists a
   `Detection` row, returns `DetectionDetail`.
6. Frontend renders `FindingsPanel` from that response; `ImageViewer` draws
   the boxes over the *original* local preview (not a re-fetched annotated
   image) using the returned pixel coordinates — one fewer network round trip
   before the user sees results.

## Data flow: training → serving

```
ml/data/raw/archive/ (your Kaggle download)
        │  data/prepare_dataset.py
        ▼
ml/data/processed/data.yaml  (merged, validated axial+coronal+sagittal)
        │  train.py
        ▼
ml/runs/train/tumor_yolo11/weights/best.pt
        │  (point APP_MODEL_WEIGHTS at this, or mount ml/runs/ into the
        │   backend container — see docker-compose.yml)
        ▼
backend loads it once at startup → serves /api/detect
```

There is intentionally no automatic "retrain and hot-swap" pipeline here —
promoting a new checkpoint to production is a deliberate act (update
`APP_MODEL_WEIGHTS`/restart), not something that happens silently mid-flight.
