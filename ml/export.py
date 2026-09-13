"""
export.py
---------
Exports a trained checkpoint to deployment formats. Only free/local formats
by default (ONNX, TorchScript) — no proprietary/paid export targets.

Run from the `ml/` directory:
  python export.py --config configs/config.yaml --weights runs/train/tumor_yolo11/weights/best.pt
"""
import argparse
from pathlib import Path

import yaml
from ultralytics import YOLO


def load_config(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/config.yaml")
    ap.add_argument("--weights", required=True)
    ap.add_argument("--formats", nargs="+", default=None, help="overrides config.export.formats")
    args = ap.parse_args()

    cfg = load_config(args.config)
    export_cfg = cfg["export"]
    formats = args.formats or export_cfg["formats"]

    model = YOLO(args.weights)
    for fmt in formats:
        print(f"Exporting to {fmt} ...")
        path = model.export(format=fmt, imgsz=export_cfg["imgsz"], half=export_cfg["half"])
        print(f"  -> {path}")


if __name__ == "__main__":
    main()
