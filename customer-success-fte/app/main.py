"""
Customer Success Digital FTE — FastAPI application entry point.

Startup sequence (lifespan):
  1. Initialise Kafka producer
  2. Verify database connectivity
  3. Start SLA monitor background task

Shutdown sequence:
  1. Cancel SLA monitor task
  2. Flush and stop Kafka producer
  3. Dispose SQLAlchemy engine
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import get_settings
from app.database import engine
from app.logging_config import configure_logging
from app.routers import gmail, web_form, whatsapp
from app.routers.metrics import router as metrics_router
from app.a2a.router import router as a2a_router
from app.skills.router import router as skills_router
from app.services.kafka_producer import kafka_producer
from app.tasks.sla_monitor import run_sla_monitor

# Configure structured logging before anything else runs
configure_logging()

settings = get_settings()
logger = logging.getLogger(__name__)

# ── Logging ────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# ── Lifespan ───────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage startup and shutdown of external connections."""
    logger.info("Starting up …")

    # Initialize skills system
    from app.skills import initialize_skills
    initialize_skills()
    logger.info("Skills system initialized")

    # Dapr health check (optional — non-blocking)
    dapr_available = False
    try:
        from app.dapr_config import get_dapr_client
        client = get_dapr_client()
        # Quick metadata call to verify Dapr sidecar is reachable
        client.get_metadata()
        dapr_available = True
        logger.info("Dapr sidecar connected: %s", settings.dapr_grpc_endpoint)
    except ImportError:
        logger.warning("Dapr SDK not installed. Running without Dapr.")
    except Exception as exc:
        logger.warning("Dapr sidecar unreachable: %s. Running without Dapr.", exc)

    # Kafka (optional in development)
    kafka_started = False
    try:
        await kafka_producer.start()
        kafka_started = True
        logger.info("Kafka producer started")
    except Exception as exc:
        logger.warning("Kafka producer failed to start: %s. Running without Kafka.", exc)

    # DB connectivity probe
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection OK.")
    except Exception as exc:
        logger.critical("Database unreachable on startup: %s", exc)
        if kafka_started:
            await kafka_producer.stop()
        raise

    # SLA monitor background task (only if Kafka started)
    sla_task = None
    if kafka_started:
        sla_task = asyncio.create_task(run_sla_monitor(), name="sla-monitor")
        logger.info("SLA monitor started")

    logger.info("Application ready.")
    yield

    # Shutdown
    logger.info("Shutting down …")

    if sla_task:
        sla_task.cancel()
        try:
            await sla_task
        except asyncio.CancelledError:
            pass

    if kafka_started:
        await kafka_producer.stop()

    await engine.dispose()
    logger.info("Shutdown complete.")


# ── App factory ────────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="AI-powered customer support agent handling Web, Gmail, and WhatsApp.",
    # Disable interactive docs in production
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan,
)

# ── Middleware ─────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", settings.api_key_header],
)

# ── Exception handlers ─────────────────────────────────────────────────────────


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"success": False, "message": "Internal server error"},
    )


# ── Health endpoints ───────────────────────────────────────────────────────────


@app.get(
    "/health",
    tags=["Ops"],
    summary="Liveness probe",
    response_description="Always returns 200 while the process is running",
)
async def health() -> dict:
    """Kubernetes liveness probe — confirms the process is alive."""
    return {"status": "ok"}


@app.get(
    "/ready",
    tags=["Ops"],
    summary="Readiness probe",
    response_description="Returns 200 when the app is ready to serve traffic",
)
async def ready() -> dict:
    """
    Kubernetes readiness probe.
    Verifies database is reachable before marking the pod ready.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:
        logger.warning("Readiness check failed: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unavailable", "detail": "Database unreachable"},
        )
    return {"status": "ready"}


# ── Routers ────────────────────────────────────────────────────────────────────

app.include_router(web_form.router, prefix="/api",      tags=["Web Form"])
app.include_router(gmail.router,    prefix="/webhooks", tags=["Gmail"])
app.include_router(whatsapp.router, prefix="/webhooks", tags=["WhatsApp"])
app.include_router(metrics_router)                        # /metrics, /metrics/dashboard

# A2A Protocol (conditionally enabled)
if settings.a2a_enabled:
    app.include_router(a2a_router, tags=["A2A Protocol"])
    logger.info("A2A Protocol endpoints enabled")

# Skills System
app.include_router(skills_router, tags=["Skills"])
logger.info("Skills endpoints enabled")
