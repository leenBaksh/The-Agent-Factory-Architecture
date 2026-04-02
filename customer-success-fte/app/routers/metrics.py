"""
Metrics endpoints.

GET /metrics
    Prometheus text exposition format (scraped by Prometheus server or
    viewed directly for debugging).  Returns metrics aggregated over the
    requested time_range query parameter (default: 24h).

GET /metrics/dashboard
    Same data in JSON, intended for the Next.js admin dashboard.

Note: in production these endpoints should be IP-restricted or placed
behind an auth middleware. They are left unauthenticated here so a
Prometheus scrape config can reach them from inside the cluster without
additional credentials.
"""

import math
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.metrics_service import TimeRange, get_dashboard_data

router = APIRouter()
logger = logging.getLogger(__name__)

_PROMETHEUS_CONTENT_TYPE = "text/plain; version=0.0.4; charset=utf-8"


# ── Prometheus text formatter ─────────────────────────────────────────────────


def _gauge(
    name: str,
    value: float | int | None,
    description: str,
    labels: Optional[dict[str, str]] = None,
) -> str:
    """
    Render a single Prometheus gauge metric block.

    Handles None and NaN values by emitting 'NaN', which Prometheus
    treats as "no data" and does not alert on by default.
    """
    if value is None or (isinstance(value, float) and math.isnan(value)):
        raw = "NaN"
    elif isinstance(value, float):
        raw = f"{value:.6g}"
    else:
        raw = str(value)

    label_str = ""
    if labels:
        pairs = ", ".join(f'{k}="{v}"' for k, v in labels.items())
        label_str = f"{{{pairs}}}"

    return (
        f"# HELP {name} {description}\n"
        f"# TYPE {name} gauge\n"
        f"{name}{label_str} {raw}"
    )


# ── Routes ────────────────────────────────────────────────────────────────────


@router.get(
    "/metrics",
    summary="Prometheus metrics",
    tags=["Ops"],
    response_description="Metrics in Prometheus text exposition format (version 0.0.4)",
)
async def prometheus_metrics(
    time_range: TimeRange = Query(default="24h", description="Aggregation window"),
    session: AsyncSession = Depends(get_db),
) -> Response:
    """
    Expose application metrics in Prometheus text exposition format.

    All metrics are gauges computed over the requested `time_range` window.
    A Prometheus scrape job should include `?time_range=1h` (or omit for the
    default 24-hour window).
    """
    try:
        data = await get_dashboard_data(time_range=time_range, session=session)
    except Exception as exc:
        logger.error("Failed to compute Prometheus metrics: %s", exc, exc_info=True)
        return Response(
            content="# ERROR: failed to compute metrics — check application logs\n",
            media_type=_PROMETHEUS_CONTENT_TYPE,
            status_code=500,
        )

    c = data["conversations"]
    t = data["tickets"]
    a = data["agent"]
    tok = data["tokens"]
    cost = data["cost"]
    lbl = {"time_range": time_range}

    blocks = [
        _gauge(
            "csfte_conversations_total",
            c["total"],
            "Total distinct customer conversations in the time window",
            lbl,
        ),
        _gauge(
            "csfte_escalation_rate_percent",
            c["escalation_rate"],
            "Percentage of agent runs that resulted in escalation",
            lbl,
        ),
        _gauge(
            "csfte_tickets_total",
            t["total"],
            "Total support tickets created in the time window",
            lbl,
        ),
        _gauge(
            "csfte_tickets_resolved_total",
            t["resolved"],
            "Tickets resolved or closed in the time window",
            lbl,
        ),
        _gauge(
            "csfte_tickets_escalated_total",
            t["escalated"],
            "Tickets currently in escalated status",
            lbl,
        ),
        _gauge(
            "csfte_resolution_rate_percent",
            t["resolution_rate"],
            "Percentage of tickets resolved out of total created",
            lbl,
        ),
        _gauge(
            "csfte_avg_csat_score",
            t["avg_csat_score"],
            "Average customer satisfaction score (1-5 scale) from post-resolution surveys",
            lbl,
        ),
        _gauge(
            "csfte_agent_runs_total",
            a["total_runs"],
            "Total agent runs (one per inbound message processed by the AI)",
            lbl,
        ),
        _gauge(
            "csfte_avg_response_time_ms",
            a["avg_latency_ms"],
            "Average AI agent response latency in milliseconds",
            lbl,
        ),
        _gauge(
            "csfte_escalations_total",
            a["escalation_count"],
            "Total escalations triggered by the agent in the time window",
            lbl,
        ),
        _gauge(
            "csfte_tokens_total",
            tok["total"],
            "Total OpenAI tokens consumed (prompt + completion combined)",
            lbl,
        ),
        _gauge(
            "csfte_tokens_prompt_total",
            tok["prompt"],
            "Total prompt (input) tokens consumed by the AI model",
            lbl,
        ),
        _gauge(
            "csfte_tokens_completion_total",
            tok["completion"],
            "Total completion (output) tokens generated by the AI model",
            lbl,
        ),
        _gauge(
            "csfte_estimated_cost_usd_total",
            cost["total_usd"],
            "Estimated total OpenAI API cost in USD for the time window",
            lbl,
        ),
        _gauge(
            "csfte_estimated_cost_per_conversation_usd",
            cost["per_conversation_usd"],
            "Estimated average OpenAI API cost per conversation in USD",
            lbl,
        ),
    ]

    content = "\n\n".join(blocks) + "\n"
    return Response(content=content, media_type=_PROMETHEUS_CONTENT_TYPE)


@router.get(
    "/metrics/dashboard",
    summary="Dashboard metrics (JSON)",
    tags=["Ops"],
)
async def dashboard_metrics(
    time_range: TimeRange = Query(default="24h", description="Aggregation window"),
    session: AsyncSession = Depends(get_db),
) -> dict:
    """
    Return the same metrics as /metrics but as structured JSON.
    Designed for the Next.js admin dashboard to consume directly.
    """
    return await get_dashboard_data(time_range=time_range, session=session)


@router.get(
    "/metrics/sla-breaches",
    summary="SLA breaches list",
    tags=["Ops"],
)
async def sla_breaches(
    session: AsyncSession = Depends(get_db),
) -> list:
    """
    Return list of SLA breaches for the dashboard.
    Returns empty list if no breaches exist.
    """
    # TODO: Implement actual SLA breach detection logic
    return []
