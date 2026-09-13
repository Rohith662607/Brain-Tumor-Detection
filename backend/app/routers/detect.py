"""
routers/detect.py
------------------
REPLACES backend/app/routers/detect.py (v3)

Changes from v2:
  - PDF is now built by report_pdf.render_pdf() (in-backend, branded,
    includes Scan ID + Findings & Recommendations) instead of calling into
    ml/predict.py's write_pdf_report(). ml/ is still never touched.
  - The DB record is created (to get its numeric Scan ID) BEFORE the PDF
    is rendered, so the ID can be printed on the PDF itself.
"""
import json
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import Session

from ..config import settings
from ..db import Detection, get_session
from ..inference_service import inference_service
from ..report_pdf import render_pdf
from ..schemas import DetectionDetail, DetectionBox

router = APIRouter(prefix="/api", tags=["detect"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}


@router.post("/detect", response_model=DetectionDetail)
async def detect(file: UploadFile = File(...), session: Session = Depends(get_session)):
    if not inference_service.is_loaded:
        raise HTTPException(503, "Model is not loaded yet — try again shortly.")

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(400, f"Unsupported file type '{file.content_type}'. Upload a JPEG or PNG.")

    contents = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(413, f"File exceeds the {settings.max_upload_mb} MB upload limit.")

    stem = uuid.uuid4().hex
    suffix = Path(file.filename).suffix or ".jpg"
    upload_path = settings.uploads_path / f"{stem}{suffix}"
    upload_path.write_bytes(contents)

    try:
        summary = inference_service.predict(upload_path)
    except Exception as e:
        raise HTTPException(500, f"Inference failed: {e}")

    annotated_path = settings.annotated_path / f"{stem}.jpg"
    inference_service.annotate(upload_path, summary, annotated_path)

    json_path = settings.reports_path / f"{stem}.json"
    json_path.write_text(json.dumps(summary, indent=2))

    record = Detection(
        original_filename=file.filename,
        upload_path=str(upload_path),
        annotated_path=str(annotated_path),
        json_report_path=str(json_path),
        tumor_detected=summary["tumor_detected"],
        num_detections=summary["num_detections"],
        total_tumor_area_pct=summary["total_tumor_area_pct"],
        detections_json=json.dumps(summary["detections"]),
        model_weights=str(settings.model_weights),
    )
    session.add(record)
    session.commit()
    session.refresh(record)  # record.id is now known — printed on the PDF itself

    pdf_path = settings.reports_path / f"{stem}.pdf"
    render_pdf(summary, annotated_path, pdf_path, detection_id=record.id)
    record.pdf_report_path = str(pdf_path)
    session.add(record)
    session.commit()
    session.refresh(record)

    return DetectionDetail(
        id=record.id,
        created_at=record.created_at,
        original_filename=record.original_filename,
        tumor_detected=record.tumor_detected,
        num_detections=record.num_detections,
        total_tumor_area_pct=record.total_tumor_area_pct,
        annotated_image_url=f"/api/image/{record.id}/annotated",
        pdf_report_url=f"/api/report/{record.id}",
        detections=[DetectionBox(**d) for d in record.detections],
        model_weights=record.model_weights,
        ai_report=record.ai_report,
    )
