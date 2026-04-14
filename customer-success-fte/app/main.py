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
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import text

from app.config import get_settings
from app.database import engine
from app.logging_config import configure_logging
from app.routers import gmail, web_form, whatsapp
from app.routers.metrics import router as metrics_router
from app.routers.notifications import router as notifications_router
from app.routers.jira import router as jira_webhook_router, api_router as jira_api_router
from app.a2a.router import router as a2a_router
from app.skills.router import router as skills_router
from app.services.kafka_producer import kafka_producer

try:
    from app.tasks.sla_monitor import run_sla_monitor
    SLA_MONITOR_AVAILABLE = True
except ImportError:
    run_sla_monitor = None
    SLA_MONITOR_AVAILABLE = False
    import logging
    logging.getLogger(__name__).warning("SLA monitor not available")

from app.mcp.initializer import initialize_mcp_servers, shutdown_mcp_servers

# Configure structured logging before anything else runs
configure_logging()

settings = get_settings()
logger = logging.getLogger(__name__)

# Track component availability (set during lifespan)
db_available = False

# ── Lifespan ───────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage startup and shutdown of external connections."""
    logger.info("Starting up …")

    # Initialize skills system
    from app.skills import initialize_skills
    initialize_skills()
    logger.info("Skills system initialized")

    # MCP servers (optional)
    mcp_manager = await initialize_mcp_servers()
    if mcp_manager:
        logger.info(f"MCP initialized with {len(mcp_manager.clients)} server(s)")

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

    # Kafka (optional in development - uses stub if aiokafka not installed)
    kafka_started = False
    try:
        await kafka_producer.start()
        kafka_started = True
        logger.info("Kafka producer started")
    except Exception as exc:
        logger.warning("Kafka producer failed to start: %s. Running without Kafka.", exc)

    # DB connectivity probe (optional in development)
    global db_available
    db_available = False
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection OK.")
        db_available = True
    except Exception as exc:
        logger.warning("Database unreachable on startup: %s. Running without DB.", exc)

    # SLA monitor background task (only if Kafka started, SLA monitor available, AND DB is up)
    sla_task = None
    if kafka_started and SLA_MONITOR_AVAILABLE and db_available:
        sla_task = asyncio.create_task(run_sla_monitor(), name="sla-monitor")
        logger.info("SLA monitor started")
    elif SLA_MONITOR_AVAILABLE:
        logger.info("SLA monitor not started (DB/Kafka unavailable)")

    logger.info("Application ready.")
    yield

    # Shutdown
    logger.info("Shutting down …")

    # Shutdown MCP servers
    await shutdown_mcp_servers()

    if sla_task:
        sla_task.cancel()
        try:
            await sla_task
        except asyncio.CancelledError:
            pass

    if kafka_started:
        await kafka_producer.stop()

    if db_available:
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


# ── Root Landing Page ──────────────────────────────────────────────────────────


@app.get(
    "/",
    tags=["Root"],
    summary="Landing page",
    response_class=HTMLResponse,
)
async def root() -> HTMLResponse:
    """Beautiful landing page with links to all endpoints."""

    # Build endpoint list dynamically
    endpoints = []

    # Health & Ops
    endpoints.append(("🏥", "Health Check", "/health", "GET", "Liveness probe", True))
    endpoints.append(("✅", "Readiness Check", "/ready", "GET", "Database readiness", db_available))

    # API Endpoints
    endpoints.append(("🌐", "Web Form", "/api/web-form", "POST", "Submit customer inquiry", False))
    endpoints.append(("📧", "Gmail Webhook", "/webhooks/gmail", "POST", "Receive Gmail events", False))
    endpoints.append(("💬", "WhatsApp Webhook", "/webhooks/whatsapp", "POST", "Receive WhatsApp messages", False))
    endpoints.append(("🔔", "Notifications", "/api/notifications/test", "POST", "Test notification", False))

    # Metrics
    endpoints.append(("📊", "Metrics", "/metrics", "GET", "Prometheus metrics", db_available))
    endpoints.append(("📈", "Dashboard", "/metrics/dashboard", "GET", "Metrics dashboard", db_available))

    # A2A Protocol
    if settings.a2a_enabled:
        endpoints.append(("🤝", "A2A Protocol", "/a2a", "POST", "Inter-FTE collaboration", False))

    # Skills
    endpoints.append(("🛠️", "Skills List", "/api/skills", "GET", "Available skills", True))

    # Jira
    if settings.jira_enabled:
        endpoints.append(("🎯", "Jira Project", "/api/jira/projects", "GET", "Jira project info", db_available))
        endpoints.append(("🎯", "Search Jira", "/api/jira/search", "GET", "Search Jira issues", db_available))
        endpoints.append(("🎯", "Create Jira Issue", "/api/jira/issues", "POST", "Create Jira issue", db_available))

    # API Docs
    if settings.debug:
        endpoints.append(("📚", "API Docs (Swagger)", "/docs", "GET", "Interactive API documentation", True))
        endpoints.append(("📖", "API Docs (ReDoc)", "/redoc", "GET", "ReDoc documentation", True))
        endpoints.append(("📄", "OpenAPI Spec", "/openapi.json", "GET", "OpenAPI 3.0 specification", True))

    # Build endpoint rows
    endpoint_rows = ""
    for icon, name, path, method, description, clickable in endpoints:
        bg_color = "#f8fafc"
        link_html = f'<a href="{path}" style="color: #3b82f6; text-decoration: none; font-family: \'Courier New\', monospace; font-size: 14px; font-weight: 500;">{path}</a>'
        if not clickable:
            link_html = f'<span style="color: #94a3b8; font-family: \'Courier New\', monospace; font-size: 14px;">{path}</span>'
            if method == "POST":
                link_html += f'<br><span style="font-size: 11px; color: #64748b;">(POST endpoint - use API client)</span>'
            elif not db_available and 'dashboard' in path:
                link_html += f'<br><span style="font-size: 11px; color: #f59e0b;">⚠️ Requires database</span>'
            elif not db_available and 'ready' in path:
                link_html += f'<br><span style="font-size: 11px; color: #f59e0b;">⚠️ Requires database</span>'

        endpoint_rows += f"""
        <tr style="background: {bg_color}; border-bottom: 1px solid #e2e8f0; opacity: {'0.5' if not clickable else '1'};">
            <td style="padding: 16px; text-align: center; font-size: 24px;">{icon}</td>
            <td style="padding: 16px;">
                <div style="font-weight: 600; color: #0f172a; margin-bottom: 4px;">{name}</div>
                <div style="font-size: 13px; color: #64748b;">{description}</div>
            </td>
            <td style="padding: 16px;">
                {link_html}
            </td>
            <td style="padding: 16px; text-align: center;">
                <span style="background: {'#dcfce7' if method == 'GET' else '#dbeafe'}; color: {'#166534' if method == 'GET' else '#1e40af'}; padding: 4px 12px; border-radius: 6px; font-size: 12px; font-weight: 600; font-family: 'Courier New', monospace;">{method}</span>
            </td>
        </tr>
        """

    # MCP status
    mcp_status = "🟢 Enabled" if settings.mcp_enabled else "🟡 Disabled"
    mcp_servers = settings.mcp_server_ids_list if settings.mcp_enabled else []
    mcp_details = f" ({', '.join(mcp_servers)})" if mcp_servers else ""

    # Jira status
    jira_status = "🟢 Connected" if settings.jira_enabled else "🟡 Disabled"
    jira_project = f" ({settings.jira_project_key})" if settings.jira_project_key else ""

    # DB status
    db_status = "🟢 Connected" if db_available else "🟡 Not Available"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{settings.app_name}</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 40px 20px;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 16px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
                color: white;
                padding: 40px;
                text-align: center;
            }}
            .header h1 {{
                font-size: 32px;
                font-weight: 700;
                margin-bottom: 8px;
            }}
            .header p {{
                font-size: 16px;
                opacity: 0.8;
            }}
            .status-bar {{
                display: flex;
                justify-content: center;
                gap: 24px;
                padding: 20px;
                background: #f8fafc;
                border-bottom: 1px solid #e2e8f0;
                font-size: 14px;
            }}
            .status-item {{
                display: flex;
                align-items: center;
                gap: 8px;
            }}
            .status-label {{
                font-weight: 600;
                color: #475569;
            }}
            .content {{ padding: 0; }}
            .section-title {{
                font-size: 20px;
                font-weight: 700;
                color: #0f172a;
                padding: 24px 40px 0;
                margin-bottom: 8px;
            }}
            .section-desc {{
                color: #64748b;
                padding: 0 40px 16px;
                font-size: 14px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 40px;
            }}
            thead {{
                background: #f1f5f9;
            }}
            th {{
                padding: 12px 16px;
                text-align: left;
                font-weight: 600;
                color: #475569;
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }}
            th:nth-child(3), th:nth-child(4) {{
                text-align: center;
            }}
            tr:hover {{
                background: #f1f5f9;
            }}
            .footer {{
                text-align: center;
                padding: 24px;
                background: #f8fafc;
                color: #64748b;
                font-size: 13px;
                border-top: 1px solid #e2e8f0;
            }}
            .footer a {{
                color: #3b82f6;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 {settings.app_name}</h1>
                <p>AI-powered customer support digital FTE</p>
            </div>
            
            <div class="status-bar">
                <div class="status-item">
                    <span class="status-label">Environment:</span>
                    <span>{settings.environment}</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Database:</span>
                    <span>{db_status}</span>
                </div>
                <div class="status-item">
                    <span class="status-label">MCP Servers:</span>
                    <span>{mcp_status}{mcp_details}</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Jira:</span>
                    <span>{jira_status}{jira_project}</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Version:</span>
                    <span>1.0.0</span>
                </div>
            </div>
            
            <div class="content">
                <h2 class="section-title">📡 Available Endpoints</h2>
                <p class="section-desc">Click on any endpoint path to test it directly in your browser</p>
                
                <table>
                    <thead>
                        <tr>
                            <th style="width: 60px;"></th>
                            <th>Endpoint</th>
                            <th>Path</th>
                            <th style="width: 100px;">Method</th>
                        </tr>
                    </thead>
                    <tbody>
                        {endpoint_rows}
                    </tbody>
                </table>
            </div>
            
            <div class="footer">
                <p>Customer Success Digital FTE v1.0.0 • Built with FastAPI • <a href="https://github.com">Documentation</a></p>
                <p style="margin-top: 8px; font-size: 12px;">🚀 All systems operational</p>
            </div>
        </div>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)


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
app.include_router(notifications_router, prefix="/api", tags=["Notifications"])
app.include_router(metrics_router)                        # /metrics, /metrics/dashboard

# A2A Protocol (conditionally enabled)
if settings.a2a_enabled:
    app.include_router(a2a_router, tags=["A2A Protocol"])
    logger.info("A2A Protocol endpoints enabled")

# Skills System
app.include_router(skills_router, tags=["Skills"])
logger.info("Skills endpoints enabled")

# Jira Integration
if settings.jira_enabled:
    app.include_router(jira_webhook_router, tags=["Jira Webhook"])
    app.include_router(jira_api_router, tags=["Jira API"])
    logger.info(f"Jira integration enabled: {settings.jira_url}")
else:
    logger.info("Jira integration disabled")
