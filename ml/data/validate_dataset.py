"""
validate_dataset.py
--------------------
Integrity checks for a YOLO-format dataset split. Catches the class of bugs
that silently wrecks training runs: orphan images/labels, out-of-range class
ids, malformed rows, and out-of-bounds/degenerate boxes.

Can be run standalone:
  python validate_dataset.py --split-dir ../data/processed/train --num-classes 2
or imported (used by prepare_dataset.py).
"""
import argparse
from pathlib import Path

try:
    from PIL import Image
    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False


def _parse_label_line(line: str, line_no: int, label_path: Path, num_classes: int, errors: list):
    parts = line.split()
    if len(parts) != 5:
        errors.append(f"{label_path.name}:{line_no}: expected 5 fields, got {len(parts)}")
        return None
    try:
        cls = int(parts[0])
        cx, cy, w, h = (float(p) for p in parts[1:])
    except ValueError:
        errors.append(f"{label_path.name}:{line_no}: non-numeric field")
        return None

    if not (0 <= cls < num_classes):
        errors.append(f"{label_path.name}:{line_no}: class id {cls} outside [0,{num_classes-1}]")
    for name, val in (("cx", cx), ("cy", cy), ("w", w), ("h", h)):
        if not (0.0 <= val <= 1.0):
            errors.append(f"{label_path.name}:{line_no}: {name}={val} outside [0,1] (not normalized?)")
    if w <= 0 or h <= 0:
        errors.append(f"{label_path.name}:{line_no}: degenerate box (w={w}, h={h})")
    # box must not extend past the image edge
    if cx - w / 2 < -1e-4 or cx + w / 2 > 1 + 1e-4 or cy - h / 2 < -1e-4 or cy + h / 2 > 1 + 1e-4:
        errors.append(f"{label_path.name}:{line_no}: box extends outside image bounds")

    return cls


def validate_split(split_dir: Path, num_classes: int) -> dict:
    split_dir = Path(split_dir)
    img_dir, lbl_dir = split_dir / "images", split_dir / "labels"
    errors = []
    class_counts = {i: 0 for i in range(num_classes)}
    n_boxes = 0

    if not img_dir.exists() or not lbl_dir.exists():
        return {"ok": False, "n_images": 0, "n_labels": 0, "n_boxes": 0,
                "class_counts": class_counts, "errors": [f"{split_dir} missing images/ or labels/"]}

    images = {p.stem: p for p in img_dir.glob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png")}
    labels = {p.stem: p for p in lbl_dir.glob("*.txt")}

    # orphan checks
    for stem in images.keys() - labels.keys():
        errors.append(f"{stem}: image has no matching label file (should be an empty .txt for background)")
    for stem in labels.keys() - images.keys():
        errors.append(f"{stem}: label file has no matching image")

    for stem, label_path in labels.items():
        text = label_path.read_text().strip()
        if not text:
            continue  # empty label = valid background image
        for i, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            cls = _parse_label_line(line, i, label_path, num_classes, errors)
            if cls is not None:
                class_counts[cls] = class_counts.get(cls, 0) + 1
                n_boxes += 1

    # spot-check a few images actually open (catches truncated/corrupt files)
    if _HAS_PIL:
        for img_path in list(images.values())[:25]:
            try:
                with Image.open(img_path) as im:
                    im.verify()
            except Exception as e:
                errors.append(f"{img_path.name}: unreadable/corrupt image ({e})")

    return {
        "ok": len(errors) == 0,
        "n_images": len(images),
        "n_labels": len(labels),
        "n_boxes": n_boxes,
        "class_counts": class_counts,
        "errors": errors,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split-dir", required=True)
    ap.add_argument("--num-classes", type=int, default=2)
    args = ap.parse_args()

    result = validate_split(Path(args.split_dir), args.num_classes)
    print(f"images={result['n_images']} labels={result['n_labels']} boxes={result['n_boxes']}")
    print(f"class_counts={result['class_counts']}")
    if result["errors"]:
        print(f"\n{len(result['errors'])} problems found:")
        for e in result["errors"]:
            print(f"  - {e}")
        raise SystemExit(1)
    print("OK — no problems found.")


if __name__ == "__main__":
    main()
