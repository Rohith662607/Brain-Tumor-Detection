# RUN_AND_DEMO_GUIDE.md
### Everything in order: set up → test → run → present

This assumes you're starting from `brain-tumor-detection-complete.zip`,
extracted somewhere on your own machine (not this sandbox — you'll need a
real GPU-capable machine or a free Colab/Kaggle GPU for the training step,
and enough disk for `torch`). Follow it top to bottom the first time.

Time estimate: ~20 min setup/testing without training, +1-3 hours if you
train a real model (mostly unattended GPU time).

---

## 0. Prerequisites

- Python 3.10+ and `pip`
- Node.js 18+ and `npm`
- (Optional but recommended) a CUDA GPU, or a free Google Colab / Kaggle
  Notebooks account for the training step
- (Optional) Docker + Docker Compose, if you want the containerized route
  instead of running things directly

Check what you have:
```bash
python3 --version
node --version
npm --version
docker --version   # optional
```

---

## 1. Unpack and place the dataset

```bash
unzip brain-tumor-detection-complete.zip -d brain-tumor-detection
cd brain-tumor-detection
```

Extract your original Kaggle-style dataset archive (the `axial_t1wce_2_class`
/ `coronal_t1wce_2_class` / `sagittal_t1wce_2_class` folders) so it looks
like:

```
ml/data/raw/archive/
├── axial_t1wce_2_class/{images,labels}/{train,test}/...
├── coronal_t1wce_2_class/{images,labels}/{train,test}/...
└── sagittal_t1wce_2_class/{images,labels}/{train,test}/...
```

If your dataset zip has a different top-level folder name, just make sure
these three plane folders end up directly under `ml/data/raw/archive/`.

---

## 2. Set up the `ml/` environment

```bash
cd ml
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

This installs `torch`/`ultralytics` — it's a few GB, give it a few minutes.

---

## 3. TEST: prepare + validate the dataset

```bash
python data/prepare_dataset.py --config configs/config.yaml --force
```

**What to look for:** it prints per-plane counts, merged totals, then a
validation pass ending in `errors=0` for train/val/test and
`Wrote .../data.yaml — dataset ready for train.py.` If you see any `errors`
count above 0, read the printed lines above it — it tells you exactly which
file and what's wrong (orphan label, bad box, etc.) before you touch
training.

✅ **Checkpoint:** `ml/data/processed/data.yaml` exists.

---

## 4. TEST: smoke-test training (a few minutes, no GPU needed)

```bash
python train.py --config configs/config.yaml --epochs 1 --batch 4 --device cpu
```

**What to look for:** it should run through 1 epoch and end with a line
pointing at `runs/train/tumor_yolo11/weights/best.pt`. This is just proving
the pipeline works end-to-end on your machine — the resulting model is
**not usable for real detection** (1 epoch teaches it almost nothing).

✅ **Checkpoint:** no crashes, `best.pt` exists somewhere under `runs/train/`.

---

## 5. RUN: real training

Pick one:

**A) You have a local GPU:**
```bash
python train.py --config configs/config.yaml
```
Defaults to 150 epochs, `yolo11s`, batch 16 — adjust in `configs/config.yaml`
if you hit out-of-memory errors (see `docs/TRAINING_GUIDE.md` for
hardware-specific presets).

**B) No local GPU — use Colab (free):**
1. Upload the `ml/` folder (or your whole repo) to Google Drive or GitHub.
2. In a new Colab notebook: Runtime → Change runtime type → GPU.
3.
   ```python
   !git clone <your-repo-url>   # or mount Drive and cd into ml/
   %cd brain-tumor-detection/ml
   !pip install -r requirements.txt -q
   !python data/prepare_dataset.py --config configs/config.yaml --force
   !python train.py --config configs/config.yaml
   ```
4. Download `runs/train/tumor_yolo11/weights/best.pt` when it finishes (or
   save it to Drive so it survives a disconnect).

This is the step that actually takes real time (expect roughly an hour or
more depending on epochs/GPU). Everything after this point is fast.

✅ **Checkpoint:** you have `ml/runs/train/tumor_yolo11/weights/best.pt`
(copy it back into your local `ml/runs/...` path if you trained on Colab).

---

## 6. TEST: evaluate the trained model

```bash
python evaluate.py --config configs/config.yaml \
  --weights runs/train/tumor_yolo11/weights/best.pt --split test
```

**What to look for:** a JSON summary printed to the terminal with `mAP50`,
`mAP50-95`, `precision`, `recall`, and per-class AP50 — plus plots saved
under `runs/val/eval_test/`. There's no fixed "pass" number, but `mAP50`
comfortably above ~0.5 on this dataset size is a reasonable sanity bar; see
`docs/TRAINING_GUIDE.md` for how to read it if something looks off (e.g.
val/train curves diverging).

---

## 7. TEST: run inference directly (before touching the web app)

```bash
python predict.py --config configs/config.yaml \
  --weights runs/train/tumor_yolo11/weights/best.pt \
  --source data/processed/test/images/axial_00095_170.jpg
```
(swap in any real image path from `data/processed/test/images/`)

**What to look for:** a printed line like
`axial_00095_170.jpg: TUMOR DETECTED (1 detection(s), 6.4% area) -> runs/predict`,
and three new files under `runs/predict/`: the annotated image, a `.json`
report, and a `.pdf` report. Open the PDF — that's exactly what the web app
will generate per-scan.

✅ **Checkpoint:** you have a working model and have seen it produce a
report, entirely from the command line, with no backend/frontend involved
yet. This is the right point to stop and confirm the model itself is good
before layering the web app on top.

---

## 8. RUN + TEST: the backend

```bash
cd ../backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set:
```
APP_MODEL_WEIGHTS=../ml/runs/train/tumor_yolo11/weights/best.pt
```

Start it:
```bash
uvicorn app.main:app --reload --port 8000
```

**Test it three ways**, in order of how much they tell you:

1. **Health check** (confirms the model loaded):
   ```bash
   curl http://localhost:8000/api/health
   ```
   Expect `{"status":"ok","model_loaded":true}`. If `model_loaded` is
   `false` or the request fails, the model path in `.env` is wrong — fix
   that before going further.

2. **Interactive docs** — open http://localhost:8000/docs in a browser,
   expand `POST /api/detect`, click "Try it out", upload a real image file,
   execute. You'll see the full JSON response right there.

3. **A real detection via curl:**
   ```bash
   curl -F "file=@../ml/data/processed/test/images/axial_00095_170.jpg" \
     http://localhost:8000/api/detect
   ```

✅ **Checkpoint:** `/api/detect` returns a JSON body with `tumor_detected`,
`detections`, etc. — and `/api/history` (in your browser or via
`curl http://localhost:8000/api/history`) now shows that detection recorded.

---

## 9. RUN + TEST: the frontend

Leave the backend running. In a new terminal:

```bash
cd frontend
npm install
cp .env.local.example .env.local   # NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
npm run dev
```

Open **http://localhost:3000**.

**Walk through all three pages to test:**
1. **New scan** (`/`) — drag an MRI image in (or click to browse). Watch the
   scan-line animation, then the bounding box(es) and findings panel appear.
   Click "Download PDF report."
2. **History** (`/history`) — your scan should now show up as a thumbnail
   with a "tumor"/"clear" badge. Try the delete button on one.
3. **Model** (`/model`) — confirms which weights are loaded, device
   (cpu/cuda), thresholds.

✅ **Checkpoint:** you've now tested the full path — dataset → trained model
→ CLI inference → API → UI — with your own eyes at every stage.

---

## 10. Alternative: run everything with Docker Compose instead of steps 8-9

Once you have `best.pt` (step 5), skip steps 8-9 and do this instead:

```bash
cd ..   # project root
cp .env.example .env
# edit .env: MODEL_WEIGHTS_PATH=/app/ml/runs/train/tumor_yolo11/weights/best.pt
docker compose up --build
```

Open http://localhost:3000. Same app, containerized. See
`docs/DEPLOYMENT_GUIDE.md` if anything about ports/volumes needs adjusting
for your machine.

---

## 11. How to show/present this

A suggested run-through, roughly in "before → after" order, for a review or
demo:

1. **Start with the audit** (`REBUILD_PLAN.md`) — a 2-minute framing: "the
   original project's inference code didn't actually run — here's why," and
   the model-strategy decision (why YOLOv11 alone instead of the original
   dual YOLO+Faster R-CNN). This is the strongest part of the story: you
   found real, specific, verifiable bugs, not vague "needs improvement."
2. **Show the dataset pipeline running live** — `prepare_dataset.py`'s
   output (step 3 above) is a good live demo: it visibly merges three
   datasets and validates them in front of the audience, ending in
   `errors=0`.
3. **Show `evaluate.py`'s output** (step 6) and contrast it with the
   original project's flat accuracy numbers — explain in one sentence why
   mAP is the right metric for detection and accuracy wasn't.
4. **Live demo the web app** (steps 8-9, or the Docker version) — upload a
   real test-set image on screen, narrate what's happening (scan animation
   → boxes appear → findings panel → PDF download), then flip to History to
   show it persisted, then Model to show what's actually loaded and serving.
5. **Close with architecture** (`docs/ARCHITECTURE.md`'s diagram) — 30
   seconds on why it's three independent pieces (`ml`/`backend`/`frontend`)
   rather than one script, and that it's Docker-deployable.

If you only have time for one live thing: step 4 (the web app demo) is the
one to not skip — everything else can be shown as documents/screenshots if
you're short on time.

---

## Troubleshooting quick reference

| Symptom | Likely cause | Fix |
|---|---|---|
| `data.yaml not found` when running `train.py` | Step 3 wasn't run, or run from the wrong directory | Run all `ml/` scripts *from inside* `ml/`, and run step 3 first |
| `prepare_dataset.py` prints `[WARN] ... not found` | `ml/data/raw/archive/` doesn't match the expected plane folder names | Re-check step 1 — the three `*_t1wce_2_class` folders must sit directly under `archive/` |
| Backend `/api/health` shows `model_loaded: false` | `APP_MODEL_WEIGHTS` in `backend/.env` points at a file that doesn't exist | Double check the path is correct and relative to `backend/` (`../ml/runs/...`) |
| Frontend can't reach the backend (network error on upload) | `NEXT_PUBLIC_API_BASE_URL` wrong, or backend not running, or CORS | Confirm backend is up (`curl .../api/health`), check `.env.local`, check `APP_CORS_ORIGINS` in backend `.env` includes `http://localhost:3000` |
| `pip install -r requirements.txt` runs out of disk | `torch` is large (~2-3GB with CUDA deps) | Use a CPU-only torch wheel (`pip install torch --index-url https://download.pytorch.org/whl/cpu`) if you don't have a GPU, or free up disk |
| Training is extremely slow | Running on CPU | Expected — CPU is for the step-4 smoke test only; use Colab/Kaggle/a real GPU for step 5 |
