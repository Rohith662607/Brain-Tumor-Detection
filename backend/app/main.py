"""
main.py
-------
FastAPI application entrypoint.

Run from the `backend/` directory:
  uvicorn app.main:app --reload --port 8000

Interactive API docs then live at http://localhost:8000/docs (auto-generated
by FastAPI — nothing to write by hand for API_DOCUMENTATION.md's basics).
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import init_db
from .inference_service import inference_service
from .routers import detect, history, system


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    inference_service.load()  # loads the model exactly once for the process lifetime
    yield


app = FastAPI(
    title="Brain Tumor Detection API",
    description="Upload an MRI slice, get back tumor location, confidence, and a downloadable report.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(detect.router)
app.include_router(history.router)
app.include_router(system.router)


@app.get("/")
def root():
    return {"service": "brain-tumor-detection-api", "docs": "/docs"}
