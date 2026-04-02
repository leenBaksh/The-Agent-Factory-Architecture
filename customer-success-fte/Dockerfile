# ══════════════════════════════════════════════════════════════════════════════
# Customer Success Digital FTE — Dockerfile
# Multi-stage build: builder compiles C-extension packages; runtime is lean.
# ══════════════════════════════════════════════════════════════════════════════

# ── Stage 1: builder ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

# gcc is required by asyncpg (C extension)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Install packages into /install so they can be cleanly copied to the runtime stage
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# curl is used by the HEALTHCHECK instruction below
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy compiled site-packages and console scripts from the builder
COPY --from=builder /install /usr/local

WORKDIR /app

# Copy application source
COPY app/ ./app/
COPY db/  ./db/

# Placeholder directory for Gmail OAuth credential files (mounted at runtime)
RUN mkdir -p /app/credentials

# Run as a non-root user
RUN useradd --system --uid 1001 --no-create-home appuser \
 && chown -R appuser:appuser /app
USER appuser

# Tune Python runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

EXPOSE 8000

HEALTHCHECK --interval=20s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

# Default command: FastAPI via Uvicorn.
# Worker and response-handler containers override this via `command:` in compose.
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--loop", "uvloop", \
     "--http", "httptools"]
