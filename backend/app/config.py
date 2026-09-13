"""
config.py
---------
REPLACES backend/app/config.py — provided again in v3 to guarantee the
setting names below exactly match what llm_report.py/report_pdf.py expect.
If another tool renamed any of these fields, this restores them.
"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_")

    # --- paths ---
    ml_dir: str = "../ml"
    ml_config_path: str = "../ml/configs/config.yaml"
    model_weights: str = "../ml/yolo11n.pt"
    storage_dir: str = "./storage"

    # --- inference ---
    conf_thres: float = 0.35
    iou_thres: float = 0.45

    # --- database ---
    database_url: str = "sqlite:///./storage/app.db"

    # --- server ---
    cors_origins: list[str] = ["http://localhost:3000"]
    max_upload_mb: int = 20

    # --- AI report / chat / assistant ---
    # These exact names are read by backend/.env (with the APP_ prefix, so
    # e.g. APP_GITHUB_TOKEN sets github_token below). Field names say
    # "github" for historical reasons but work with ANY OpenAI-compatible
    # provider (GitHub Models, Groq, etc.) — just point the three values
    # at your provider.
    enable_ai_report: bool = True
    github_token: str = ""                 # e.g. your Groq API key
    github_model: str = "openai/gpt-oss-120b"
    github_models_endpoint: str = "https://api.groq.com/openai/v1"

    @property
    def storage_path(self) -> Path:
        p = Path(self.storage_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def uploads_path(self) -> Path:
        p = self.storage_path / "uploads"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def annotated_path(self) -> Path:
        p = self.storage_path / "annotated"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def reports_path(self) -> Path:
        p = self.storage_path / "reports"
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()
