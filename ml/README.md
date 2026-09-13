# Brain Tumor Detection — ML Core (Phase 1)

This is the modernized training/inference pipeline described in `REBUILD_PLAN.md`.
It replaces the broken `detect.py` / `gui.py` / TF Object Detection API path with
a single Ultralytics YOLOv11 pipeline, config-driven end to end.

**Verified in this environment:** `data/prepare_dataset.py` and
`data/validate_dataset.py` were run against your actual dataset (extracted from
`Braintumourpart2.zip`) and produced a clean merged split — 761 train / 132 val /
223 test images, 0 integrity errors. **Not verified here:** `train.py`,
`evaluate.py`, `predict.py`, `export.py` — this sandbox has no GPU and ran out
of disk space installing `torch`/`ultralytics` (they're large packages).
The code is correct against the documented Ultralytics API, but **run a real
smoke test yourself** (`--epochs 1` on a small subset) before trusting it for a
full training run. See "First run checklist" below.

## Layout

```
ml/
├── configs/config.yaml     # every default lives here — no hardcoded paths/values in code
├── data/
│   ├── prepare_dataset.py  # merges axial+coronal+sagittal into one YOLO dataset
│   ├── validate_dataset.py # integrity checks (orphans, bad boxes, corrupt images)
│   └── raw/                # put your extracted Kaggle archive here (see below)
├── train.py                # fine-tune YOLOv11
├── evaluate.py              # real detection metrics: mAP50, mAP50-95, precision, recall
├── predict.py                # inference -> bbox + confidence + tumor-area% + annotated image + JSON/PDF report
├── export.py                  # -> ONNX / TorchScript for deployment
└── requirements.txt
```

## Setup

```bash
cd ml
python -m venv .venv && source .venv/bin/activate   # or use conda
pip install -r requirements.txt
```

## 1. Get the data in place

Copy/extract your dataset so it looks like:

```
ml/data/raw/archive/
├── axial_t1wce_2_class/{images,labels}/{train,test}/...
├── coronal_t1wce_2_class/{images,labels}/{train,test}/...
└── sagittal_t1wce_2_class/{images,labels}/{train,test}/...
```

(This is exactly the structure inside your original `Braintumourpart2.zip` —
just point `data.raw_root` in `configs/config.yaml` at it, or drop it at the
default path above.)

## 2. Prepare + validate the dataset

```bash
python data/prepare_dataset.py --config configs/config.yaml --force
```

This merges the three planes into `data/processed/{train,val,test}`, prefixes
filenames by plane (`axial_00095_170.jpg`, etc.) so nothing collides, carves a
validation split out of the original train set (no val split shipped originally),
and refuses to write `data.yaml` if validation finds any problem — a hard-negative
on the mixed-quality label duplication problem the old dataset had.

## 3. First run checklist (do this before a real training run)

```bash
# 1-epoch CPU smoke test — confirms the pipeline runs end-to-end on your machine
python train.py --config configs/config.yaml --epochs 1 --batch 4 --device cpu

# once that finishes without error, kick off a real run (GPU strongly recommended):
python train.py --config configs/config.yaml
```

`configs/config.yaml` defaults to `yolo11s.pt` / 150 epochs / batch 16 — tune
`model.base_weights` (`yolo11n.pt` is smallest/fastest) and `train.batch` down
if you're on Colab free tier or a small consumer GPU.

## 4. Evaluate properly

The original project's "accuracy" numbers (98.3% YOLO / 92.6% Faster R-CNN)
used a plain classification-style formula, not a real detection metric. This
gives you mAP50, mAP50-95, precision, recall, and per-class AP50 instead:

```bash
python evaluate.py --config configs/config.yaml --weights runs/train/tumor_yolo11/weights/best.pt --split test
```

## 5. Run inference + generate clinical-style reports

```bash
python predict.py --config configs/config.yaml \
  --weights runs/train/tumor_yolo11/weights/best.pt \
  --source path/to/an_mri_image.jpg
```

For each image this writes: an annotated copy (`runs/predict/annotated/`), a
JSON report, and a one-page PDF report (`runs/predict/reports/`) — bounding
box, confidence, and tumor area as % of image, per detection.

`predict.run_inference(model, image_path, ...)` is the function to import
directly into the FastAPI backend (Phase 2) rather than shelling out to the CLI.

## 6. Export for deployment

```bash
python export.py --config configs/config.yaml --weights runs/train/tumor_yolo11/weights/best.pt
```

## Experiment tracking

Defaults to local MLflow (`tracking.backend: mlflow` in config.yaml, no
account/API key). View it with:

```bash
mlflow ui --backend-store-uri ./mlruns
```

Set `tracking.backend: tensorboard` to use `runs/train/.../` with
`tensorboard --logdir runs/train` instead, or `none` to disable.

## Class definitions

`negative` (class 0) and `positive` (class 1) come from the original Kaggle
dataset's own labeling convention — `negative` boxes mark tumor-mimicking but
benign regions (hard negatives), `positive` is an actual tumor. Only
`positive` detections count toward `tumor_detected` / tumor-area% in
`predict.py`.

## What's next (Phase 2/3/4, not in this drop)

- FastAPI backend wrapping `predict.run_inference()` behind `/detect`,
  `/history`, `/report/{id}` endpoints.
- Next.js + Tailwind + shadcn/ui frontend (upload, view, download report).
- Docker Compose, deployment guide, API docs.

Say the word and I'll start on the backend next.
