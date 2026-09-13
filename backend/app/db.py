"""
db.py
-----
REPLACES backend/app/db.py (v2 — adds chat_history_json)

New in v2: `chat_history_json`, storing the per-scan chat conversation as a
JSON array of {"role": ..., "content": ...} turns — same pattern as the
existing `detections_json` column. Nullable/defaulted, so this is additive.
"""
import json
from datetime import datetime
from typing import Optional
from pathlib import Path
from sqlmodel import Field, SQLModel, Session, create_engine, select

from .config import settings


class Detection(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    original_filename: str
    upload_path: str
    annotated_path: Optional[str] = None
    json_report_path: Optional[str] = None
    pdf_report_path: Optional[str] = None

    tumor_detected: bool
    num_detections: int
    total_tumor_area_pct: float

    # full per-box detection list, stored as JSON text (SQLite has no native
    # array/JSON column type without an extension) — use `detections` property
    # to get it back as a list of dicts.
    detections_json: str = "[]"

    model_weights: str

    # AI-generated narrative report text (GitHub Models). Nullable — null
    # until the user explicitly clicks "Generate report" (v2: on-demand,
    # not auto-generated on upload).
    ai_report: Optional[str] = None

    # Per-scan chat conversation, as a JSON array of {"role","content"} turns.
    chat_history_json: str = "[]"

    @property
    def detections(self) -> list[dict]:
        return json.loads(self.detections_json)

    @property
    def chat_history(self) -> list[dict]:
        return json.loads(self.chat_history_json or "[]")


# Make sure the SQLite database directory exists before SQLAlchemy connects.
if settings.database_url.startswith("sqlite:///"):
    db_path = settings.database_url.replace("sqlite:///", "", 1)
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)


def init_db():
    # Ensure storage/database directory exists before creating tables.
    if settings.database_url.startswith("sqlite:///"):
        db_path = settings.database_url.replace("sqlite:///", "", 1)
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    SQLModel.metadata.create_all(engine)
    # NOTE: create_all() only creates NEW tables, it does not alter existing
    # ones. If you already have an existing storage/app.db from before this
    # change, either:
    #   (a) delete storage/app.db and let it recreate (loses old history), or
    #   (b) run manually via `sqlite3 storage/app.db`:
    #       ALTER TABLE detection ADD COLUMN chat_history_json TEXT DEFAULT '[]';


def get_session():
    with Session(engine) as session:
        yield session


def list_detections(session: Session, limit: int = 50, offset: int = 0) -> list[Detection]:
    stmt = select(Detection).order_by(Detection.created_at.desc()).offset(offset).limit(limit)
    return list(session.exec(stmt))


def get_detection(session: Session, detection_id: int) -> Optional[Detection]:
    return session.get(Detection, detection_id)
