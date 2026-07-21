# Backend image for deploy (#35). Bakes the vector index at build time so the
# container is answer-ready on boot — the free-tier host has no persistent disk
# to run `embed_store` against on first request.
FROM python:3.11-slim

# System deps: tesseract for OCR (#8), libmagic for `unstructured`.
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr libmagic1 poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY data/ ./data/

WORKDIR /app/backend

# Build the Chroma index into the image. Skips gracefully if data is absent.
RUN python -m ingestion.embed_store || echo "WARN: index build skipped at build time"

ENV API_HOST=0.0.0.0
EXPOSE 8000

# $PORT is provided by Render/Fly; default to 8000 locally.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
