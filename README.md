# Brain Tumor Detection — YOLOv11, FastAPI, Next.js

A modernized, from-scratch rebuild of a college object-detection project
(originally YOLOv5 + Faster R-CNN, broken as shipped) into a working
detect → serve → view pipeline. Full audit of the original project,
rationale for every technical decision, and what changed: **`REBUILD_PLAN.md`**.

## What this is

Upload an MRI slice (axial, coronal, or sagittal) → get back tumor location,
confidence, area as a % of the image, an annotated copy, and a downloadable
PDF report.

## Structure

Three independently-runnable phases — see **`docs/PROJECT_STRUCTURE.md`**
for the full tree and **`docs/ARCHITECTURE.md`** for how/why they fit
together:

| Phase | Folder | What it is |
|---|---|---|
| 1 | [`ml/`](ml/README.md) | Dataset prep, YOLOv11 training, evaluation, inference, export |
| 2 | [`backend/`](backend/README.md) | FastAPI service wrapping the model behind a REST API |
| 3 | [`frontend/`](frontend/README.md) | Next.js UI — upload, view detections, history, reports |

## Quickstart

```bash
# 1. Get the dataset in place and train (see ml/README.md for detail)
cd ml && pip install -r requirements.txt
python data/prepare_dataset.py --config configs/config.yaml --force
python train.py --config configs/config.yaml --epochs 1 --device cpu --batch 4   # smoke test first
python train.py --config configs/config.yaml                                       # real run

# 2. Bring up the API + UI
cd ..
cp .env.example .env   # set MODEL_WEIGHTS_PATH to your trained best.pt
docker compose up --build
```

Open http://localhost:3000. Full instructions, including non-Docker local
setup and free hosting options: **`docs/DEPLOYMENT_GUIDE.md`**.

## Documentation index

- **`RUN_AND_DEMO_GUIDE.md`** — start here for a single, ordered, copy-paste
  walkthrough: setup → test → run → present, with a checkpoint after every
  stage and a troubleshooting table at the end.
- **`REBUILD_PLAN.md`** — audit of the original project, what was reused vs.
  rewritten, and the YOLOv11-over-Faster-R-CNN model strategy decision.
- **`DATASET_IMPROVEMENT_GUIDE.md`** — dataset-specific findings (class
  balance, duplicates found, relabeling/expansion recommendations).
- **`API_SETUP_GUIDE.md`** — confirms no paid API keys are required anywhere.
- **`docs/ARCHITECTURE.md`** — system design and the reasoning behind it.
- **`docs/TRAINING_GUIDE.md`** — hardware-specific training configs (consumer
  GPU, Colab/Kaggle free tier, CPU smoke test), how to read the results.
- **`docs/API_DOCUMENTATION.md`** — narrative companion to the backend's
  auto-generated `/docs` (Swagger UI).
- **`docs/DEPLOYMENT_GUIDE.md`** — local, Docker, GPU, and free-hosting
  instructions.

## What was verified vs. not, honestly

This was built in a sandboxed environment with no GPU and limited network
access (package registries only — no Kaggle/TCIA, no Google Fonts CDN at one
point, no room on disk for a full `torch` install at another). Rather than
claim untested code works, each phase's README says plainly what was and
wasn't actually run:

- **`ml/`**: dataset merge + validation script run against the real dataset
  (761/132/223 split, 0 integrity errors). Training/eval/predict/export
  scripts are correct against the documented Ultralytics API but not
  execution-tested here (no GPU, no disk room for `torch`).
- **`backend/`**: app construction and all 8 routes verified via FastAPI's
  actual route table. A live `/api/detect` call was not run here (same
  `torch` constraint).
- **`frontend/`**: `npm install`, full type-check, and a full production
  `next build` all passed clean in this sandbox — the most thoroughly
  verified phase, since it needs no GPU. Caught and fixed a real Next.js CVE
  (bumped 14.2.5 → 14.2.35) during that process.
- **`docker-compose.yml`** / Dockerfiles: no Docker daemon available in this
  sandbox — validated as well as possible without one (YAML syntax checked,
  build logic reviewed against each Dockerfile's actual COPY/WORKDIR paths)
  but not build-tested. Build and run these yourself before depending on them.

Run the "first run checklist" in `ml/README.md` and the smoke tests in
`backend/README.md` on your own machine before trusting this in production.
