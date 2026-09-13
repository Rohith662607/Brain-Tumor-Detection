"""
predict.py
----------
Runs tumor detection on one image or a directory of images and produces the
"clinical outputs" the project set out to deliver:
  - tumor location (bounding box, in pixel coords)
  - confidence score
  - tumor area as a % of total image area
  - an annotated copy of the image
  - a JSON detection report
  - a one-page PDF detection report (per image)

Run from the `ml/` directory:
  python predict.py --config configs/config.yaml --weights best.pt --source path/to/image_or_dir

This is the module the FastAPI backend (Phase 2) calls into directly —
`run_inference()` is the function to import for that, the CLI below is a
thin wrapper around it for local/manual use.
"""
import argparse
import json
from datetime import datetime
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO

IMG_EXTS = (".jpg", ".jpeg", ".png")


def load_config(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def run_inference(model: YOLO, image_path: Path, conf_thres: float, iou_thres: float, class_names: list):
    """Runs one image through the model and returns a structured result dict.
    This is the function the FastAPI backend should import and call directly
    (no need to shell out to this script in production)."""
    results = model.predict(source=str(image_path), conf=conf_thres, iou=iou_thres, verbose=False)
    r = results[0]

    img_w, img_h = r.orig_shape[1], r.orig_shape[0]
    img_area = img_w * img_h

    detections = []
    for box in r.boxes:
        xyxy = box.xyxy[0].tolist()
        x1, y1, x2, y2 = xyxy
        box_area = max(0.0, x2 - x1) * max(0.0, y2 - y1)
        cls_id = int(box.cls[0])
        detections.append({
            "class_id": cls_id,
            "class_name": class_names[cls_id] if cls_id < len(class_names) else str(cls_id),
            "confidence": round(float(box.conf[0]), 4),
            "bbox_xyxy": [round(v, 1) for v in xyxy],
            "area_px": round(box_area, 1),
            "area_pct_of_image": round(100.0 * box_area / img_area, 2) if img_area else None,
        })

    tumor_dets = [d for d in detections if d["class_name"] == "positive"]
    summary = {
        "image": str(image_path),
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "image_size": {"width": img_w, "height": img_h},
        "tumor_detected": len(tumor_dets) > 0,
        "num_detections": len(detections),
        "total_tumor_area_pct": round(sum(d["area_pct_of_image"] for d in tumor_dets), 2) if tumor_dets else 0.0,
        "detections": detections,
    }
    return summary, r


def annotate_image(image_path: Path, summary: dict, out_path: Path):
    im = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(im)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    for d in summary["detections"]:
        x1, y1, x2, y2 = d["bbox_xyxy"]
        color = (220, 30, 30) if d["class_name"] == "positive" else (255, 180, 0)
        draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
        label = f"{d['class_name']} {d['confidence']:.2f} ({d['area_pct_of_image']}% area)"
        draw.text((x1, max(0, y1 - 12)), label, fill=color, font=font)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    im.save(out_path)
    return out_path


def write_pdf_report(summary: dict, annotated_image_path: Path, out_path: Path):
    """One-page PDF report per image. Uses reportlab; falls back to fpdf2
    if reportlab isn't installed."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.pdfgen import canvas

        c = canvas.Canvas(str(out_path), pagesize=A4)
        width, height = A4
        y = height - 2 * cm

        c.setFont("Helvetica-Bold", 16)
        c.drawString(2 * cm, y, "Brain Tumor Detection — Report")
        y -= 1 * cm

        c.setFont("Helvetica", 10)
        c.drawString(2 * cm, y, f"Image: {Path(summary['image']).name}")
        y -= 0.5 * cm
        c.drawString(2 * cm, y, f"Generated: {summary['timestamp_utc']}")
        y -= 0.5 * cm
        c.drawString(2 * cm, y, f"Tumor detected: {'YES' if summary['tumor_detected'] else 'NO'}")
        y -= 0.5 * cm
        c.drawString(2 * cm, y, f"Total tumor area: {summary['total_tumor_area_pct']}% of image")
        y -= 1 * cm

        try:
            img_w = 12 * cm
            img_h = img_w * summary["image_size"]["height"] / summary["image_size"]["width"]
            c.drawImage(str(annotated_image_path), 2 * cm, y - img_h, width=img_w, height=img_h)
            y -= img_h + 1 * cm
        except Exception:
            pass

        c.setFont("Helvetica-Bold", 11)
        c.drawString(2 * cm, y, "Detections")
        y -= 0.6 * cm
        c.setFont("Helvetica", 9)
        for i, d in enumerate(summary["detections"], start=1):
            line = (f"{i}. {d['class_name']}  conf={d['confidence']}  "
                    f"bbox={d['bbox_xyxy']}  area={d['area_pct_of_image']}%")
            c.drawString(2 * cm, y, line)
            y -= 0.45 * cm
            if y < 2 * cm:
                c.showPage()
                y = height - 2 * cm

        c.showPage()
        c.save()
    except ImportError:
        from fpdf import FPDF

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "Brain Tumor Detection - Report", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 8, f"Image: {Path(summary['image']).name}", ln=True)
        pdf.cell(0, 8, f"Generated: {summary['timestamp_utc']}", ln=True)
        pdf.cell(0, 8, f"Tumor detected: {'YES' if summary['tumor_detected'] else 'NO'}", ln=True)
        pdf.cell(0, 8, f"Total tumor area: {summary['total_tumor_area_pct']}% of image", ln=True)
        try:
            pdf.image(str(annotated_image_path), w=150)
        except Exception:
            pass
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Detections", ln=True)
        pdf.set_font("Helvetica", "", 9)
        for i, d in enumerate(summary["detections"], start=1):
            pdf.multi_cell(0, 6, f"{i}. {d['class_name']} conf={d['confidence']} "
                                  f"bbox={d['bbox_xyxy']} area={d['area_pct_of_image']}%")
        pdf.output(str(out_path))

    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/config.yaml")
    ap.add_argument("--weights", required=True)
    ap.add_argument("--source", required=True, help="image file or directory")
    args = ap.parse_args()

    cfg = load_config(args.config)
    pred_cfg = cfg["predict"]
    class_names = cfg["data"]["names"]

    model = YOLO(args.weights)
    source = Path(args.source)
    images = [source] if source.is_file() else sorted(
        p for p in source.iterdir() if p.suffix.lower() in IMG_EXTS
    )
    if not images:
        raise SystemExit(f"No images found at {source}")

    out_dir = Path(pred_cfg["project_dir"])
    for img_path in images:
        summary, _ = run_inference(model, img_path, pred_cfg["conf_thres"], pred_cfg["iou_thres"], class_names)

        annotated_path = out_dir / "annotated" / img_path.name
        if pred_cfg["save_annotated"]:
            annotate_image(img_path, summary, annotated_path)
            summary["annotated_image"] = str(annotated_path)

        if pred_cfg["save_report_json"]:
            json_path = out_dir / "reports" / f"{img_path.stem}.json"
            json_path.parent.mkdir(parents=True, exist_ok=True)
            with open(json_path, "w") as f:
                json.dump(summary, f, indent=2)

        if pred_cfg["save_report_pdf"] and pred_cfg["save_annotated"]:
            pdf_path = out_dir / "reports" / f"{img_path.stem}.pdf"
            write_pdf_report(summary, annotated_path, pdf_path)

        status = "TUMOR DETECTED" if summary["tumor_detected"] else "no tumor"
        print(f"{img_path.name}: {status} "
              f"({summary['num_detections']} detection(s), "
              f"{summary['total_tumor_area_pct']}% area) -> {out_dir}")


if __name__ == "__main__":
    main()
