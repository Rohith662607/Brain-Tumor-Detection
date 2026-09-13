# Build from the project root:
#   docker build -f backend/Dockerfile -t brain-tumor-backend .
# (docker-compose.yml at the project root already does this for you)
#
# The image bundles ml/ alongside backend/ because inference_service.py
# imports ml/predict.py directly at runtime (see backend/README.md) — it's
# not a pip package, so it has to physically sit next to the backend code.
FROM python:3.12-slim

# libgl1/libglib2.0-0: needed by opencv (a torchvision/ultralytics transitive
# dependency) even with the "headless" wheel, on a from-scratch slim image.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY ml/ ./ml/
COPY backend/ ./backend/

WORKDIR /app/backend
RUN pip install --no-cache-dir -r requirements.txt

ENV APP_ML_DIR=/app/ml
ENV APP_ML_CONFIG_PATH=/app/ml/configs/config.yaml
ENV APP_STORAGE_DIR=/app/backend/storage

EXPOSE 8000

# --workers 1: the model is loaded into process memory once at startup
# (see app/inference_service.py); scale via multiple containers behind a
# load balancer, not multiple uvicorn workers sharing one loaded model.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
