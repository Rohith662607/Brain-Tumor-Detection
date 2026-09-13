"""
evaluate.py
-----------
Runs proper detection evaluation (mAP50, mAP50-95, precision, recall, per-class
breakdown) via Ultralytics' built-in validator — replacing the original
project's flat "(TP+TN)/(TP+TN+FP+FN)" accuracy figure, which isn't a valid
metric for object detection (it doesn't account for localization quality or
handle multiple/zero objects per image correctly).

Run from the `ml/` directory:
  python evaluate.py --config configs/config.yaml --weights runs/train/tumor_yolo11/weights/best.pt
  python evaluate.py --config configs/config.yaml --weights best.pt --split test
"""
import argparse
import json
from pathlib import Path

import yaml
from ultralytics import YOLO


def load_config(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/config.yaml")
    ap.add_argument("--weights", required=True, help="path to a trained .pt checkpoint")
    ap.add_argument("--split", default=None, help="train/val/test — defaults to config.evaluate.split")
    args = ap.parse_args()

    cfg = load_config(args.config)
    eval_cfg = cfg["evaluate"]
    split = args.split or eval_cfg["split"]

    data_yaml = Path(cfg["data"]["processed_root"]) / "data.yaml"
    if not data_yaml.exists():
        raise SystemExit(f"{data_yaml} not found. Run data/prepare_dataset.py first.")

    model = YOLO(args.weights)
    metrics = model.val(
        data=str(data_yaml),
        split=split,
        conf=eval_cfg["conf_thres"],
        iou=eval_cfg["iou_thres"],
        project=eval_cfg["project_dir"],
        name=f"eval_{split}",
        exist_ok=True,
        plots=True,
    )

    names = cfg["data"]["names"]
    summary = {
        "split": split,
        "weights": args.weights,
        "precision": float(metrics.box.mp),
        "recall": float(metrics.box.mr),
        "mAP50": float(metrics.box.map50),
        "mAP50-95": float(metrics.box.map),
        "per_class": {
            names[i]: {
                "AP50": float(metrics.box.ap50[i]) if i < len(metrics.box.ap50) else None,
            }
            for i in range(len(names))
        },
    }

    out_dir = Path(eval_cfg["project_dir"]) / f"eval_{split}"
    out_path = out_dir / "metrics_summary.json"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)

    print("\n=== Evaluation summary ===")
    print(json.dumps(summary, indent=2))
    print(f"\nFull report + plots: {out_dir}")


if __name__ == "__main__":
    main()
