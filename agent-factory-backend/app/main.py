"""
Agent Factory Backend — FastAPI application entry point

This backend provides the API for the Agent Factory Dashboard,
aggregating metrics from all Digital FTE instances.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.logging_config import configure_logging

# Configure structured logging before anything else runs
configure_logging()

settings = get_settings()
logger = logging.getLogger(__name__)


# ── Lifespan ───────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage startup and shutdown."""
    logger.info("Starting up Agent Factory Backend...")
    
    # Register FTE instances
    await register_fte_instances()
    
    logger.info("Agent Factory Backend ready.")
    yield
    
    # Shutdown
    logger.info("Shutting down Agent Factory Backend...")
    await unregister_fte_instances()
    logger.info("Shutdown complete.")


async def register_fte_instances():
    """Register all known FTE instances."""
    import random
    from datetime import datetime
    from app.services.fte_registry import fte_registry

    now = datetime.now()
    
    # Register FTEs with dynamic metrics
    ftes = [
        {
            "id": "customer-success-1",
            "name": "Customer Success FTE",
            "type": "customer-success",
            "status": "running",
            "version": "1.0.0",
            "url": settings.customer_success_fte_url,
            "uptime_seconds": 86400 + random.randint(0, 3600),
            "last_health_check": now.isoformat(),
            "metrics": {
                "messages_per_minute": round(10 + random.random() * 5, 1),
                "avg_latency_ms": random.randint(200, 280),
                "error_rate": round(0.01 + random.random() * 0.03, 2),
                "active_conversations": random.randint(5, 12),
            },
        },
        {
            "id": "sales-support-1",
            "name": "Sales Support FTE",
            "type": "sales",
            "status": "running",
            "version": "1.2.0",
            "url": "http://localhost:8001",
            "uptime_seconds": 172800 + random.randint(0, 3600),
            "last_health_check": now.isoformat(),
            "metrics": {
                "messages_per_minute": round(6 + random.random() * 4, 1),
                "avg_latency_ms": random.randint(150, 220),
                "error_rate": round(0.005 + random.random() * 0.02, 2),
                "active_conversations": random.randint(3, 8),
            },
        },
        {
            "id": "technical-support-1",
            "name": "Technical Support FTE",
            "type": "technical-support",
            "status": "running",
            "version": "0.9.5",
            "url": "http://localhost:8002",
            "uptime_seconds": 43200 + random.randint(0, 3600),
            "last_health_check": now.isoformat(),
            "metrics": {
                "messages_per_minute": round(12 + random.random() * 6, 1),
                "avg_latency_ms": random.randint(280, 380),
                "error_rate": round(0.05 + random.random() * 0.06, 2),
                "active_conversations": random.randint(8, 15),
            },
        },
    ]
    
    for fte in ftes:
        await fte_registry.register(fte)

    logger.info(f"Registered FTE instances: {len(fte_registry.instances)}")


async def unregister_fte_instances():
    """Unregister all FTE instances."""
    from app.services.fte_registry import fte_registry
    await fte_registry.clear()


# ── App factory ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Agent Factory Backend",
    version="1.0.0",
    description="Central backend API for the Agent Factory Dashboard",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)


# ── Middleware ─────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
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


@app.get("/health", tags=["Ops"])
async def health() -> dict:
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/ready", tags=["Ops"])
async def ready() -> dict:
    """Readiness probe."""
    return {"status": "ready"}


# ── Metrics endpoints ──────────────────────────────────────────────────────────

@app.get("/metrics/dashboard", tags=["Metrics"])
async def get_dashboard_metrics():
    """Get aggregated dashboard metrics from all FTEs."""
    from app.routers.metrics import aggregate_dashboard_metrics
    return await aggregate_dashboard_metrics()


@app.get("/metrics/sla-breaches", tags=["Metrics"])
async def get_sla_breaches():
    """Get SLA breaches from all FTEs."""
    from app.routers.metrics import get_all_sla_breaches
    return await get_all_sla_breaches()


# ── FTE endpoints ──────────────────────────────────────────────────────────────

@app.get("/api/a2a/ftes", tags=["FTE"])
async def list_ftes():
    """List all FTE instances."""
    from app.routers.ftes import list_all_ftes
    return await list_all_ftes()


@app.post("/api/a2a/ftes", tags=["FTE"])
async def create_fte(fte_data: dict):
    """Create a new FTE instance."""
    from app.routers.ftes import create_new_fte
    return await create_new_fte(fte_data)


@app.get("/api/a2a/ftes/{fte_id}", tags=["FTE"])
async def get_fte(fte_id: str):
    """Get a specific FTE instance."""
    from app.routers.ftes import get_fte_by_id
    return await get_fte_by_id(fte_id)


@app.delete("/api/a2a/ftes/{fte_id}", tags=["FTE"])
async def delete_fte(fte_id: str):
    """Delete an FTE instance."""
    from app.routers.ftes import delete_fte_by_id
    return await delete_fte_by_id(fte_id)


# ── Skills endpoints ───────────────────────────────────────────────────────────

@app.get("/api/skills", tags=["Skills"])
async def list_skills():
    """List all available skills."""
    from app.routers.skills import list_all_skills
    return await list_all_skills()


@app.get("/api/skills/{skill_id}", tags=["Skills"])
async def get_skill(skill_id: str):
    """Get a specific skill."""
    from app.routers.skills import get_skill_by_id
    return await get_skill_by_id(skill_id)


# ── A2A Protocol endpoints ─────────────────────────────────────────────────────

if settings.a2a_enabled:
    from app.routers.a2a import router as a2a_router
    app.include_router(a2a_router, prefix="/a2a", tags=["A2A Protocol"])
    logger.info("A2A Protocol endpoints enabled")
