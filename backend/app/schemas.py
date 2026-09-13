"""
schemas.py
----------
REPLACES backend/app/schemas.py (v3 — adds AssistantChatRequest)
"""
from datetime import datetime

from pydantic import BaseModel


class DetectionBox(BaseModel):
    class_id: int
    class_name: str
    confidence: float
    bbox_xyxy: list[float]
    area_px: float
    area_pct_of_image: float | None


class DetectionSummary(BaseModel):
    id: int
    created_at: datetime
    original_filename: str
    tumor_detected: bool
    num_detections: int
    total_tumor_area_pct: float
    annotated_image_url: str | None
    pdf_report_url: str | None


class DetectionDetail(DetectionSummary):
    detections: list[DetectionBox]
    model_weights: str
    ai_report: str | None = None


class HistoryPage(BaseModel):
    total_returned: int
    limit: int
    offset: int
    items: list[DetectionSummary]


class ModelInfo(BaseModel):
    weights_path: str
    class_names: list[str]
    image_size: int
    conf_threshold: float
    iou_threshold: float
    device: str


class HealthStatus(BaseModel):
    status: str
    model_loaded: bool


# --- AI report / chat ---

class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str | None = None  # None on GET (just returning existing history)
    history: list[ChatMessage]


class AssistantChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []
