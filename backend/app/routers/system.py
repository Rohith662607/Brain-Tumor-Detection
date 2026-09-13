"""
routers/system.py
------------------
Model metadata (for the frontend's "Model Information" page) and a health
check (for Docker/uptime monitoring).
"""
from fastapi import APIRouter

from ..config import settings
from ..inference_service import inference_service
from ..schemas import ModelInfo, HealthStatus

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/model/info", response_model=ModelInfo)
def model_info():
    return ModelInfo(
        weights_path=settings.model_weights,
        class_names=inference_service.class_names,
        image_size=640,
        conf_threshold=settings.conf_thres,
        iou_threshold=settings.iou_thres,
        device=inference_service.device,
    )


@router.get("/health", response_model=HealthStatus)
def health():
    return HealthStatus(status="ok", model_loaded=inference_service.is_loaded)
