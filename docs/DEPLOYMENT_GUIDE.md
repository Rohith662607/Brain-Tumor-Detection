# DEPLOYMENT_GUIDE.md

All options here are free/local — no paid account or subscription required
to get this running (see `API_SETUP_GUIDE.md`).

## 0. Prerequisite: train a model first

Deploying without a trained checkpoint gives you a working API/UI that runs
inference with a stock, non-tumor-tuned YOLOv11 checkpoint — fine for
smoke-testing the plumbing, useless for actual tumor detection. Do
`ml/README.md`'s training steps first; everything below assumes you have
`ml/runs/train/tumor_yolo11/weights/best.pt`.

## 1. Local setup (no Docker)

```bash
# terminal 1 — backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env: APP_MODEL_WEIGHTS=../ml/runs/train/tumor_yolo11/weights/best.pt
uvicorn app.main:app --reload --port 8000

# terminal 2 — frontend
cd frontend
npm install
cp .env.local.example .env.local   # NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
npm run dev
```

Open http://localhost:3000.

## 2. GPU setup notes

- **Training** wants a GPU; `ml/train.py` auto-detects CUDA (`device: ""` in
  `config.yaml`) or pass `--device 0`. CPU training works but is slow — use
  `--device cpu --epochs 1` only to smoke-test the pipeline runs.
- **Serving/inference** is fine on CPU for a single-user demo (YOLOv11n/s at
  640px is well under a second per image on a modern CPU). If you do have a
  GPU on the serving machine, the backend's `inference_service.py` picks it
  up automatically via `torch.cuda.is_available()` — no config needed.
- **Docker + GPU**: the provided `backend/Dockerfile` is CPU-only (no CUDA
  base image, to keep the default path free/simple/portable). For GPU
  serving in Docker, swap the base image for `nvidia/cuda:12.x-runtime` +
  install the matching `torch` CUDA wheel, and add
  `deploy.resources.reservations.devices` (or `--gpus all`) to the compose
  service — the NVIDIA Container Toolkit needs to be installed on the host
  either way.

## 3. Docker Compose (recommended for anything beyond local dev)

```bash
# from the project root
cp .env.example .env    # see below
docker compose up --build
```

`.env` (project root, not `backend/.env`):
```
MODEL_WEIGHTS_PATH=/app/ml/runs/train/tumor_yolo11/weights/best.pt
PUBLIC_API_BASE_URL=http://localhost:8000
```

`docker-compose.yml` mounts `./ml/runs` and `./ml/configs` read-only into the
backend container, so retraining a model and restarting the container is all
it takes to serve a new checkpoint — no image rebuild needed. The dataset
itself (`ml/data/`) is deliberately **not** copied into any image (see
`.dockerignore`) — training happens on your machine/Colab/Kaggle, not inside
this stack.

## 4. Free hosting options

None of these need a paid tier for a small demo deployment:

- **Hugging Face Spaces** (Docker SDK) — good fit for the backend; upload
  your trained `best.pt` as a Space file or via a dataset repo, point
  `APP_MODEL_WEIGHTS` at it. Free CPU tier is sufficient for occasional
  demo use.
- **Render / Railway free tiers** — both support "deploy from Dockerfile";
  point at `backend/Dockerfile` and `frontend/Dockerfile` as two services.
  Free tiers sleep on inactivity — fine for a portfolio demo, not for
  production uptime.
- **Local Linux/Windows server** — `docker compose up -d` and put it behind
  whatever reverse proxy/HTTPS setup you already have (e.g. Caddy, nginx).
- **Google Colab** — not a hosting target for the web app, but the natural
  place to actually *run* `ml/train.py` on a free GPU; export `best.pt` and
  download it to deploy elsewhere.

Whichever host you pick, remember to set the frontend's
`NEXT_PUBLIC_API_BASE_URL` (a **build-time** arg, see `frontend/Dockerfile`)
to wherever the backend actually ends up, and add that frontend origin to the
backend's `APP_CORS_ORIGINS`.

## 5. Environment variable reference

| Variable | Where | Purpose |
|---|---|---|
| `APP_MODEL_WEIGHTS` | backend | Path to the `.pt` checkpoint to serve |
| `APP_ML_DIR` / `APP_ML_CONFIG_PATH` | backend | Where the sibling `ml/` project lives |
| `APP_DATABASE_URL` | backend | SQLite (default) or Postgres connection string |
| `APP_STORAGE_DIR` | backend | Where uploads/annotated images/reports are written |
| `APP_CORS_ORIGINS` | backend | JSON array of allowed frontend origins |
| `NEXT_PUBLIC_API_BASE_URL` | frontend | Backend URL — **baked in at build time**, not runtime |

## 6. Health checks

`GET /api/health` → `{"status": "ok", "model_loaded": true}`. The Docker
Compose file already wires this into a container healthcheck; the frontend
container waits for it before starting.
