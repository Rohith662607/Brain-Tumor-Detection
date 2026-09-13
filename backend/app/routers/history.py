"""
routers/history.py
-------------------
REPLACES backend/app/routers/history.py (v3)

New in v3:
  - generate_ai_report() now also regenerates the PDF (via report_pdf) so
    the download includes the AI Findings & Recommendations section, not
    just the original detection-only PDF.
  - POST /api/assistant/chat — the new sidebar Assistant. Stateless on the
    server: the frontend sends the full conversation each time (like the
    per-scan chat), and this endpoint additionally builds a compact index
    of ALL scans plus full detail for any scan mentioned by ID or filename,
    so the assistant can answer specific questions about past scans.
  - Added logging around the AI calls so failures are visible in the
    backend terminal, not just as a generic frontend error.
"""
import json
import logging
import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlmodel import Session

from ..config import settings
from ..db import Detection, get_session, list_detections, get_detection
from ..llm_report import generate_report, answer_question, assistant_reply
from ..report_pdf import render_pdf
from ..schemas import (
    DetectionSummary,
    DetectionDetail,
    DetectionBox,
    HistoryPage,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    AssistantChatRequest,
)

router = APIRouter(prefix="/api", tags=["history"])
logger = logging.getLogger("uvicorn.error")


def _to_summary(record: Detection) -> DetectionSummary:
    return DetectionSummary(
        id=record.id,
        created_at=record.created_at,
        original_filename=record.original_filename,
        tumor_detected=record.tumor_detected,
        num_detections=record.num_detections,
        total_tumor_area_pct=record.total_tumor_area_pct,
        annotated_image_url=f"/api/image/{record.id}/annotated" if record.annotated_path else None,
        pdf_report_url=f"/api/report/{record.id}" if record.pdf_report_path else None,
    )


def _to_detail(record: Detection) -> DetectionDetail:
    return DetectionDetail(
        **_to_summary(record).model_dump(),
        detections=[DetectionBox(**d) for d in json.loads(record.detections_json)],
        model_weights=record.model_weights,
        ai_report=record.ai_report,
    )


def _load_summary(record: Detection) -> dict:
    if record.json_report_path and Path(record.json_report_path).exists():
        return json.loads(Path(record.json_report_path).read_text())
    return {
        "image": record.original_filename,
        "timestamp_utc": record.created_at.isoformat() + "Z",
        "image_size": {"width": 0, "height": 0},
        "tumor_detected": record.tumor_detected,
        "num_detections": record.num_detections,
        "total_tumor_area_pct": record.total_tumor_area_pct,
        "detections": json.loads(record.detections_json),
    }


@router.get("/history", response_model=HistoryPage)
def get_history(limit: int = 50, offset: int = 0, session: Session = Depends(get_session)):
    limit = max(1, min(limit, 200))
    records = list_detections(session, limit=limit, offset=offset)
    return HistoryPage(
        total_returned=len(records),
        limit=limit,
        offset=offset,
        items=[_to_summary(r) for r in records],
    )


@router.get("/history/{detection_id}", response_model=DetectionDetail)
def get_history_detail(detection_id: int, session: Session = Depends(get_session)):
    record = get_detection(session, detection_id)
    if record is None:
        raise HTTPException(404, "Detection not found.")
    return _to_detail(record)


@router.delete("/history/{detection_id}")
def delete_history(detection_id: int, session: Session = Depends(get_session)):
    record = get_detection(session, detection_id)
    if record is None:
        raise HTTPException(404, "Detection not found.")
    session.delete(record)
    session.commit()
    return {"deleted": detection_id}


@router.get("/image/{detection_id}/annotated")
def get_annotated_image(detection_id: int, session: Session = Depends(get_session)):
    record = get_detection(session, detection_id)
    if record is None or not record.annotated_path:
        raise HTTPException(404, "Annotated image not found.")
    return FileResponse(record.annotated_path, media_type="image/jpeg")


@router.get("/report/{detection_id}")
def get_pdf_report(detection_id: int, session: Session = Depends(get_session)):
    record = get_detection(session, detection_id)
    if record is None or not record.pdf_report_path:
        raise HTTPException(404, "Report not found.")
    return FileResponse(
        record.pdf_report_path,
        media_type="application/pdf",
        filename=f"tumor_report_{detection_id}.pdf",
    )


# --- AI report (on-demand) ---

@router.post("/history/{detection_id}/report", response_model=DetectionDetail)
def generate_ai_report(detection_id: int, session: Session = Depends(get_session)):
    record = get_detection(session, detection_id)
    if record is None:
        raise HTTPException(404, "Detection not found.")

    summary = _load_summary(record)
    try:
        report = generate_report(summary)
    except Exception as e:  # noqa: BLE001 — surfaced to the caller deliberately
        logger.warning(f"AI report generation failed for scan #{detection_id}: {e}")
        raise HTTPException(502, f"AI report generation failed: {e}")

    record.ai_report = report
    session.add(record)
    session.commit()
    session.refresh(record)

    # Regenerate the PDF so the download includes the AI findings too.
    # If this step fails, the text report is still saved — just log it.
    try:
        pdf_path = Path(record.pdf_report_path) if record.pdf_report_path else settings.reports_path / f"{detection_id}.pdf"
        render_pdf(summary, Path(record.annotated_path), pdf_path, detection_id=record.id, ai_report=report)
        record.pdf_report_path = str(pdf_path)
        session.add(record)
        session.commit()
        session.refresh(record)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"PDF regeneration failed for scan #{detection_id}, text report is still saved: {e}")

    return _to_detail(record)


# --- Per-scan chat ---

@router.get("/history/{detection_id}/chat", response_model=ChatResponse)
def get_chat(detection_id: int, session: Session = Depends(get_session)):
    record = get_detection(session, detection_id)
    if record is None:
        raise HTTPException(404, "Detection not found.")
    return ChatResponse(reply=None, history=[ChatMessage(**m) for m in record.chat_history])


@router.post("/history/{detection_id}/chat", response_model=ChatResponse)
def post_chat(detection_id: int, body: ChatRequest, session: Session = Depends(get_session)):
    record = get_detection(session, detection_id)
    if record is None:
        raise HTTPException(404, "Detection not found.")
    if not body.message.strip():
        raise HTTPException(400, "Message cannot be empty.")

    summary = _load_summary(record)
    history = record.chat_history

    try:
        reply = answer_question(summary, history, body.message.strip())
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Chat failed for scan #{detection_id}: {e}")
        raise HTTPException(502, f"Chat failed: {e}")

    history.append({"role": "user", "content": body.message.strip()})
    history.append({"role": "assistant", "content": reply})
    record.chat_history_json = json.dumps(history)
    session.add(record)
    session.commit()

    return ChatResponse(reply=reply, history=[ChatMessage(**m) for m in history])


# --- Global Assistant (app-wide, grounded in the full history index) ---

def _history_index(session: Session) -> str:
    records = list_detections(session, limit=200, offset=0)
    if not records:
        return "(no scans in history yet)"
    return "\n".join(
        f"#{r.id} | {r.original_filename} | {r.created_at.date()} | "
        f"{'TUMOR DETECTED' if r.tumor_detected else 'no tumor'} | "
        f"{r.num_detections} detection(s) | {r.total_tumor_area_pct}% area"
        for r in records
    )


def _matched_detail_blocks(session: Session, message: str) -> str:
    """Looks for scan IDs (numbers) or filename fragments in the question
    and pulls full detail for any match, so the assistant can answer
    specifics rather than just the compact index."""
    blocks = []
    seen_ids: set[int] = set()

    for n in re.findall(r"\d+", message):
        record = get_detection(session, int(n))
        if record and record.id not in seen_ids:
            seen_ids.add(record.id)
            blocks.append(
                f"--- Scan #{record.id} ({record.original_filename}) ---\n"
                f"Tumor detected: {record.tumor_detected} | Detections: {record.num_detections} "
                f"| Area: {record.total_tumor_area_pct}%\n"
                f"AI report on file: {record.ai_report or '(not generated yet)'}"
            )

    words = [w.strip(".,?!\"'()") for w in message.split() if len(w.strip(".,?!\"'()")) > 5]
    if words:
        for r in list_detections(session, limit=200):
            if r.id in seen_ids:
                continue
            if any(w.lower() in r.original_filename.lower() for w in words):
                seen_ids.add(r.id)
                blocks.append(
                    f"--- Scan #{r.id} ({r.original_filename}) ---\n"
                    f"Tumor detected: {r.tumor_detected} | Detections: {r.num_detections} "
                    f"| Area: {r.total_tumor_area_pct}%\n"
                    f"AI report on file: {r.ai_report or '(not generated yet)'}"
                )

    return "\n\n".join(blocks)


@router.post("/assistant/chat", response_model=ChatResponse)
def assistant_chat(body: AssistantChatRequest, session: Session = Depends(get_session)):
    if not body.message.strip():
        raise HTTPException(400, "Message cannot be empty.")

    history_index = _history_index(session)
    matched = _matched_detail_blocks(session, body.message)
    prior = [m.model_dump() for m in body.history]

    try:
        reply = assistant_reply(prior, body.message.strip(), history_index, matched)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Assistant failed: {e}")
        raise HTTPException(502, f"Assistant failed: {e}")

    updated = body.history + [
        ChatMessage(role="user", content=body.message.strip()),
        ChatMessage(role="assistant", content=reply),
    ]
    return ChatResponse(reply=reply, history=updated)
