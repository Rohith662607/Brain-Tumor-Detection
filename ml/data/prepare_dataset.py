"""
prepare_dataset.py
-------------------
Merges the three raw plane datasets (axial / coronal / sagittal — each with
its own images/{train,test} + labels/{train,test} in YOLO format) into a
single, validated, unified dataset ready for training.

Why merge instead of training 3 separate models:
  - Each plane individually is small (a few hundred images). Pooling them
    gives the model far more examples of what a tumor looks like, and a
    single deployed model is simpler to serve than three.
  - The plane is kept as a filename prefix (not silently dropped) so it's
    still recoverable for analysis, and so identically-numbered files from
    different planes (e.g. axial "62.jpg" and coronal "62.jpg") never collide.

What this script does:
  1. Walks raw_root/<plane>/images/{train,test} and matching labels/.
  2. Copies each image to processed_root/<split>/images/<plane>_<name>,
     and its label (or an empty label file, for background/negative images)
     to processed_root/<split>/labels/<plane>_<name>.txt.
  3. Carves a validation split out of "train" (val_fraction), since the
     source only ships train/test.
  4. Runs integrity checks (see validate_dataset.py) and refuses to write
     a data.yaml if anything looks corrupt.
  5. Writes processed_root/data.yaml for Ultralytics YOLO.

Usage:
  python prepare_dataset.py --config ../configs/config.yaml
"""
import argparse
import random
import re
import shutil
from pathlib import Path

import yaml

from validate_dataset import validate_split


def load_config(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def collect_pairs(plane_root: Path, split: str):
    """Return list of (image_path, label_path_or_None) for one plane/split."""
    img_dir = plane_root / "images" / split
    lbl_dir = plane_root / "labels" / split
    pairs = []
    if not img_dir.exists():
        return pairs
    for img_path in sorted(img_dir.glob("*")):
        if img_path.suffix.lower() not in (".jpg", ".jpeg", ".png"):
            continue
        lbl_path = lbl_dir / f"{img_path.stem}.txt"
        pairs.append((img_path, lbl_path if lbl_path.exists() else None))
    return pairs

def group_key(stem: str) -> str:
    """Group images from the same scan/patient together so a split never
    separates near-duplicate slices of the same scan across train/val."""
    stem = re.sub(r"\s*\(\d+\)$", "", stem)          # strip Windows dup suffix " (2)"
    m = re.match(r"^(\d+)_\d+$", stem)                 # e.g. "00018_101" -> patient "00018"
    if m:
        return m.group(1)
    return stem                                        # fallback: whole stem is its own group

def write_pair(img_path: Path, lbl_path, out_img_dir: Path, out_lbl_dir: Path, prefix: str):
    out_name = f"{prefix}_{img_path.name}"
    out_img = out_img_dir / out_name
    shutil.copy2(img_path, out_img)

    out_lbl = out_lbl_dir / f"{prefix}_{img_path.stem}.txt"
    if lbl_path is not None:
        shutil.copy2(lbl_path, out_lbl)
    else:
        # No tumor annotation for this image -> valid YOLO "background" image:
        # an empty label file, NOT a missing one (missing means "unlabeled",
        # empty means "confirmed no objects"). The original project never
        # made this distinction explicit — we do.
        out_lbl.touch()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="../configs/config.yaml")
    ap.add_argument("--force", action="store_true", help="wipe processed_root if it exists")
    args = ap.parse_args()

    cfg = load_config(args.config)
    data_cfg = cfg["data"]
    raw_root = Path(data_cfg["raw_root"]).resolve()
    processed_root = Path(data_cfg["processed_root"]).resolve()
    val_fraction = float(data_cfg["val_fraction"])
    planes = data_cfg["planes"]
    random.seed(cfg["project"]["seed"])

    if processed_root.exists():
        if args.force:
            shutil.rmtree(processed_root)
        else:
            raise SystemExit(
                f"{processed_root} already exists. Re-run with --force to rebuild it."
            )

    for split in ("train", "val", "test"):
        (processed_root / split / "images").mkdir(parents=True, exist_ok=True)
        (processed_root / split / "labels").mkdir(parents=True, exist_ok=True)

    stats = {"train": 0, "val": 0, "test": 0, "background_images": 0}

    for plane in planes:
        plane_root = raw_root / plane
        if not plane_root.exists():
            print(f"[WARN] {plane_root} not found — skipping this plane.")
            continue
        prefix = plane.replace("_t1wce_2_class", "")  # -> axial / coronal / sagittal

        # --- test split passes straight through ---
        test_pairs = collect_pairs(plane_root, "test")
        for img_path, lbl_path in test_pairs:
            write_pair(
                img_path, lbl_path,
                processed_root / "test" / "images",
                processed_root / "test" / "labels",
                prefix,
            )
            stats["test"] += 1
            if lbl_path is None:
                stats["background_images"] += 1

        # --- train split gets carved into train/val ---
# --- train split gets carved into train/val, grouped by scan/patient
        # so near-duplicate slices of the same scan never land on both sides ---
        train_pairs = collect_pairs(plane_root, "train")

        groups = {}
        for img_path, lbl_path in train_pairs:
            key = group_key(img_path.stem)
            groups.setdefault(key, []).append((img_path, lbl_path))

        group_keys = list(groups.keys())
        random.shuffle(group_keys)
        n_val_groups = int(len(group_keys) * val_fraction)
        val_keys, train_keys = set(group_keys[:n_val_groups]), set(group_keys[n_val_groups:])

        val_pairs = [p for k in val_keys for p in groups[k]]
        train_only_pairs = [p for k in train_keys for p in groups[k]]

        for img_path, lbl_path in train_only_pairs:
            write_pair(
                img_path, lbl_path,
                processed_root / "train" / "images",
                processed_root / "train" / "labels",
                prefix,
            )
            stats["train"] += 1
            if lbl_path is None:
                stats["background_images"] += 1

        for img_path, lbl_path in val_pairs:
            write_pair(
                img_path, lbl_path,
                processed_root / "val" / "images",
                processed_root / "val" / "labels",
                prefix,
            )
            stats["val"] += 1
            if lbl_path is None:
                stats["background_images"] += 1

        print(f"[{plane}] train={len(train_only_pairs)} val={len(val_pairs)} test={len(test_pairs)}")

    print("\n=== Merged dataset totals ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    # --- integrity checks before we trust this dataset for training ---
    print("\n=== Validating processed dataset ===")
    ok = True
    for split in ("train", "val", "test"):
        result = validate_split(processed_root / split, num_classes=data_cfg["nc"])
        ok = ok and result["ok"]
        print(f"[{split}] images={result['n_images']} labels={result['n_labels']} "
              f"boxes={result['n_boxes']} class_counts={result['class_counts']} "
              f"errors={len(result['errors'])}")
        for e in result["errors"][:10]:
            print(f"    - {e}")
        if len(result["errors"]) > 10:
            print(f"    ... and {len(result['errors']) - 10} more")

    if not ok:
        raise SystemExit(
            "\nDataset validation FAILED — see errors above. "
            "data.yaml was NOT written. Fix the source data or the errors "
            "and re-run with --force."
        )

    data_yaml = {
        "path": str(processed_root),
        "train": "train/images",
        "val": "val/images",
        "test": "test/images",
        "nc": data_cfg["nc"],
        "names": data_cfg["names"],
    }
    with open(processed_root / "data.yaml", "w") as f:
        yaml.safe_dump(data_yaml, f, sort_keys=False)

    print(f"\nWrote {processed_root / 'data.yaml'} — dataset ready for train.py.")


if __name__ == "__main__":
    main()
