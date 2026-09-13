"""
inference_service.py
---------------------
Loads the YOLO model exactly once (at app startup, see main.py's lifespan)
and wraps the Phase 1 `ml/predict.py` functions — run_inference(),
annotate_image(), write_pdf_report() — instead of duplicating that logic.

This is the module that talks to `ultralytics`; every router calls into this,
never into `ultralytics`/`ml/predict.py` directly, so there's exactly one
place that owns the loaded model.
"""
import sys
from pathlib import Path

import yaml

from .config import settings

# Make the sibling `ml/` project importable (it's not a pip package).
_ml_dir = str(Path(settings.ml_dir).resolve())
if _ml_dir not in sys.path:
    sys.path.insert(0, _ml_dir)


class InferenceService:
    def __init__(self):
        self._model = None
        self._class_names: list[str] = []
        self._device: str = "cpu"

    def load(self):
        """Called once from the FastAPI lifespan handler on startup."""
        from ultralytics import YOLO  # imported lazily so `ml_dir` is on sys.path first

        with open(settings.ml_config_path) as f:
            cfg = yaml.safe_load(f)
        self._class_names = cfg["data"]["names"]

        weights_path = Path(settings.model_weights)
        if not weights_path.exists():
            raise FileNotFoundError(
                f"Model weights not found at {weights_path}. Train a model first "
                f"(see ml/README.md) or point APP_MODEL_WEIGHTS at a valid checkpoint."
            )
        self._model = YOLO(str(weights_path))
        try:
            import torch
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            self._device = "cpu"

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    @property
    def class_names(self) -> list[str]:
        return self._class_names

    @property
    def device(self) -> str:
        return self._device

    def predict(self, image_path: Path) -> dict:
        """Runs detection on one image. Returns the same summary dict shape as
        ml/predict.py's run_inference(), i.e. what the API serializes."""
        from predict import run_inference  # ml/predict.py

        if self._model is None:
            raise RuntimeError("Model not loaded — call .load() first.")

        summary, _raw = run_inference(
            self._model, image_path, settings.conf_thres, settings.iou_thres, self._class_names
        )
        return summary

    def annotate(self, image_path: Path, summary: dict, out_path: Path) -> Path:
        from predict import annotate_image  # ml/predict.py
        return annotate_image(image_path, summary, out_path)

    def write_pdf(self, summary: dict, annotated_image_path: Path, out_path: Path) -> Path:
        from predict import write_pdf_report  # ml/predict.py
        return write_pdf_report(summary, annotated_image_path, out_path)


# module-level singleton, populated by main.py's lifespan on startup
inference_service = InferenceService()
