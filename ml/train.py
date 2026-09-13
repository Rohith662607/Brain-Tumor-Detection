"""
train.py
--------
Config-driven YOLOv11 fine-tuning for tumor detection.

Run from the `ml/` directory:
  python train.py --config configs/config.yaml
  python train.py --config configs/config.yaml --resume        # resume last run
  python train.py --config configs/config.yaml --epochs 50 --device cpu  # override any config value

Notes:
  - Requires data/processed/data.yaml (run data/prepare_dataset.py first).
  - Works on CPU (slow — fine for a smoke test with --epochs 1) or GPU
    (auto-detected; pass --device 0 / 0,1 / cpu to force).
  - Logs to MLflow locally by default (no account/API key). Set
    tracking.backend: tensorboard or none in config.yaml to change that.
"""
import argparse
from pathlib import Path

import yaml
from ultralytics import YOLO


def load_config(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def apply_overrides(cfg: dict, args: argparse.Namespace) -> dict:
    train_cfg = cfg["train"]
    for key in ("epochs", "batch", "device", "resume"):
        val = getattr(args, key, None)
        if val is not None:
            train_cfg[key] = val
    if args.weights:
        cfg["model"]["base_weights"] = args.weights
    return cfg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/config.yaml")
    ap.add_argument("--epochs", type=int, default=None)
    ap.add_argument("--batch", type=int, default=None)
    ap.add_argument("--device", default=None)
    ap.add_argument("--weights", default=None, help="override model.base_weights, or a checkpoint to resume from")
    ap.add_argument("--resume", action="store_true", default=None)
    args = ap.parse_args()

    cfg = load_config(args.config)
    cfg = apply_overrides(cfg, args)

    data_yaml = Path(cfg["data"]["processed_root"]) / "data.yaml"
    if not data_yaml.exists():
        raise SystemExit(
            f"{data_yaml} not found. Run `python data/prepare_dataset.py --config {args.config}` first."
        )

    train_cfg = cfg["train"]
    aug = train_cfg["augment"]

    # --- experiment tracking ---
    tracking = cfg.get("tracking", {})
    if tracking.get("backend") == "mlflow":
        import mlflow
        mlflow.set_tracking_uri(tracking.get("mlflow_tracking_uri", "./mlruns"))
        mlflow.set_experiment(tracking.get("experiment_name", "brain-tumor-yolo11"))
        # Ultralytics has native MLflow integration triggered by these env vars;
        # this also lets you `mlflow ui` locally to compare runs.
        import os
        os.environ["MLFLOW_EXPERIMENT_NAME"] = tracking.get("experiment_name", "brain-tumor-yolo11")
        os.environ["MLFLOW_TRACKING_URI"] = tracking.get("mlflow_tracking_uri", "./mlruns")

    model = YOLO(cfg["model"]["base_weights"])

    results = model.train(
        data=str(data_yaml),
        imgsz=cfg["model"]["imgsz"],
        epochs=train_cfg["epochs"],
        batch=train_cfg["batch"],
        patience=train_cfg["patience"],
        workers=train_cfg["workers"],
        device=train_cfg["device"],
        amp=train_cfg["amp"],
        resume=bool(train_cfg["resume"]),
        optimizer=train_cfg["optimizer"],
        lr0=train_cfg["lr0"],
        cos_lr=train_cfg["cos_lr"],
        project=train_cfg["project_dir"],
        name=train_cfg["run_name"],
        seed=cfg["project"]["seed"],
        exist_ok=True,
        hsv_h=aug["hsv_h"], hsv_s=aug["hsv_s"], hsv_v=aug["hsv_v"],
        degrees=aug["degrees"], translate=aug["translate"], scale=aug["scale"],
        fliplr=aug["fliplr"], flipud=aug["flipud"],
        mosaic=aug["mosaic"], mixup=aug["mixup"],
        plots=True,
    )

    best = Path(train_cfg["project_dir"]) / train_cfg["run_name"] / "weights" / "best.pt"
    print(f"\nTraining complete.")
    print(f"Best checkpoint: {best if best.exists() else '(check runs dir — training may have been interrupted)'}")
    print(f"Results/plots:   {Path(train_cfg['project_dir']) / train_cfg['run_name']}")


if __name__ == "__main__":
    main()
