# ── Stage: base Python image ───────────────────────────────────────────────
# python:3.11-slim = full Python but without docs/tests (~50MB vs ~900MB full)
FROM python:3.11-slim

# ── System dependencies ─────────────────────────────────────────────────────
# API container only needs PDF processing tools — NO browser.
# Scraper runs locally (headless=false) so humans can solve captchas.
# Removing Playwright saves ~2.2GB and cuts build time from 10min → 2min.
#   curl          → healthcheck probes
#   poppler-utils → pdf2image needs this to convert PDFs to images
#   tesseract-ocr → pytesseract OCR fallback for scanned PDFs
#   libgl1        → opencv requires this OpenGL library
RUN apt-get update && apt-get install -y \
    curl \
    poppler-utils \
    tesseract-ocr \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ────────────────────────────────────────────────────────
WORKDIR /app

# ── Dependency installation (layer cache optimisation) ───────────────────────
# Copy ONLY the dependency file first.
# If your code changes but pyproject.toml doesn't → pip install is skipped (cached).
# If you copy everything first → pip install reruns on every code change (slow).
COPY pyproject.toml .
RUN pip install --no-cache-dir .
# --no-cache-dir → don't store pip's download cache inside the image (saves ~100MB)

# ── Application code ─────────────────────────────────────────────────────────
# Copy code AFTER pip install so code changes don't invalidate the pip cache.
COPY ingestion_engine/ ./ingestion_engine/

# ── Port declaration ─────────────────────────────────────────────────────────
# EXPOSE documents which port this service uses. Docker Compose reads this.
# It does NOT publish the port — that happens in docker-compose.yml.
EXPOSE 8000

# ── Startup command ──────────────────────────────────────────────────────────
# --host 0.0.0.0 = listen on all interfaces inside the container
#                  (not just localhost, which would be unreachable from outside)
# --port 8000    = match the EXPOSE above
CMD ["uvicorn", "ingestion_engine.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
