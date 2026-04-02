"""
Metrics service.

Provides three public interfaces:
  - update_metrics(conversation_id, session)
      Aggregates all agent_metric rows for a conversation and stamps the
      latest row with a conversation-level summary (tokens, cost, CSAT, etc.).
      Called by the worker after each successful agent run.

  - get_dashboard_data(time_range, session)
      Queries agent_metrics + tickets and returns a structured dict of
      aggregated dashboard metrics for the requested time window.
      Used by the /metrics/dashboard JSON endpoint.

  - log_agent_action(action, **kwargs)
      Emits a structured log event via structlog for significant agent
      decisions (escalations, resolutions, guardrail trips, tool calls).

Metrics tracked per conversation summary:
  - total_messages / agent runs
  - token usage (prompt + completion)
  - estimated USD cost (based on model pricing)
  - avg response latency
  - escalation flag
  - resolution flag
  - CSAT score (from satisfaction survey)
"""

import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Any, Literal, Optional

import structlog
from sqlalchemy import Integer, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import AgentMetric, Message, Ticket, TicketStatus

logger = structlog.get_logger(__name__)
settings = get_settings()


# ── Cost estimation ────────────────────────────────────────────────────────────

def _estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """
    Return estimated USD cost for one agent run.
    
    Uses current OpenAI pricing (updated dynamically via config).
    Falls back to default rates if model not found.
    """
    # Default rates (GPT-4o baseline)
    in_rate = settings.openai_input_cost_per_1k.get(model, 0.0025)
    out_rate = settings.openai_output_cost_per_1k.get(model, 0.010)
    return (prompt_tokens / 1_000 * in_rate) + (completion_tokens / 1_000 * out_rate)


# ── update_metrics ────────────────────────────────────────────────────────────


async def update_metrics(
    conversation_id: Any,  # uuid.UUID
    session: AsyncSession,
) -> None:
    """
    Aggregate per-conversation stats and persist them to the latest
    agent_metric row's metadata_.

    Computes:
      - total tokens and estimated cost across all agent runs
      - average and total latency
      - escalation flag
      - resolution flag (from linked tickets)
      - CSAT score (from ticket survey_rating metadata)

    Failures are caught and logged — never propagated.
    """
    try:
        # Load all AgentMetric rows for this conversation via Message join
        result = await session.execute(
            select(AgentMetric)
            .join(Message, AgentMetric.message_id == Message.id)
            .where(Message.conversation_id == conversation_id)
            .order_by(AgentMetric.created_at.asc())
        )
        metrics = result.scalars().all()

        if not metrics:
            return

        # ── Aggregate token and latency stats ─────────────────────────────────
        total_tokens      = sum(m.total_tokens for m in metrics)
        prompt_tokens     = sum(m.prompt_tokens for m in metrics)
        completion_tokens = sum(m.completion_tokens for m in metrics)
        total_latency_ms  = sum(m.latency_ms for m in metrics)
        avg_latency_ms    = total_latency_ms // len(metrics)
        was_escalated     = any(m.was_escalated for m in metrics)

        # ── Cost estimate ─────────────────────────────────────────────────────
        estimated_cost_usd = sum(
            _estimate_cost(m.model, m.prompt_tokens, m.completion_tokens)
            for m in metrics
        )

        # ── Ticket resolution + CSAT ──────────────────────────────────────────
        ticket_result = await session.execute(
            select(Ticket).where(Ticket.conversation_id == conversation_id)
        )
        tickets = ticket_result.scalars().all()

        was_resolved = any(
            t.status in (TicketStatus.resolved, TicketStatus.closed)
            for t in tickets
        )

        csat_scores = [
            t.metadata_.get("survey_rating")
            for t in tickets
            if t.metadata_.get("survey_rating") is not None
        ]
        avg_csat = (
            round(sum(csat_scores) / len(csat_scores), 2) if csat_scores else None
        )

        # ── Stamp the most recent metric row ──────────────────────────────────
        latest = metrics[-1]
        latest.metadata_ = {
            **latest.metadata_,
            "conversation_summary": {
                "conversation_id":    str(conversation_id),
                "total_runs":         len(metrics),
                "total_tokens":       total_tokens,
                "prompt_tokens":      prompt_tokens,
                "completion_tokens":  completion_tokens,
                "avg_latency_ms":     avg_latency_ms,
                "was_escalated":      was_escalated,
                "was_resolved":       was_resolved,
                "estimated_cost_usd": round(estimated_cost_usd, 6),
                "avg_csat_score":     avg_csat,
                "computed_at":        datetime.now(timezone.utc).isoformat(),
            },
        }

        logger.info(
            "Metrics updated",
            conversation_id=str(conversation_id),
            total_tokens=total_tokens,
            estimated_cost_usd=round(estimated_cost_usd, 6),
            was_resolved=was_resolved,
            was_escalated=was_escalated,
        )

    except Exception as exc:
        logger.warning(
            "Failed to update metrics",
            conversation_id=str(conversation_id),
            error=str(exc),
        )


# ── get_dashboard_data ────────────────────────────────────────────────────────

TimeRange = Literal["1h", "24h", "7d", "30d"]

_RANGE_DELTA: dict[str, timedelta] = {
    "1h":  timedelta(hours=1),
    "24h": timedelta(hours=24),
    "7d":  timedelta(days=7),
    "30d": timedelta(days=30),
}


async def get_dashboard_data(
    time_range: TimeRange,
    session: AsyncSession,
) -> dict:
    """
    Return aggregated dashboard metrics for the requested time window.

    Queries:
      - agent_metrics — token usage, latency, run count, escalation count
      - messages      — distinct conversation count (via agent_metrics join)
      - tickets       — resolution rate, CSAT, escalation count
    """
    since = datetime.now(timezone.utc) - _RANGE_DELTA.get(time_range, timedelta(hours=24))

    # ── Agent metrics aggregation ─────────────────────────────────────────────
    agg = (
        await session.execute(
            select(
                func.count(AgentMetric.id).label("total_runs"),
                func.coalesce(func.sum(AgentMetric.total_tokens), 0).label("total_tokens"),
                func.coalesce(func.sum(AgentMetric.prompt_tokens), 0).label("prompt_tokens"),
                func.coalesce(func.sum(AgentMetric.completion_tokens), 0).label("completion_tokens"),
                func.coalesce(func.avg(AgentMetric.latency_ms), 0).label("avg_latency_ms"),
                func.coalesce(
                    func.sum(cast(AgentMetric.was_escalated, Integer)), 0
                ).label("escalation_count"),
            ).where(AgentMetric.created_at >= since)
        )
    ).one()

    total_runs        = int(agg.total_runs)
    total_tokens      = int(agg.total_tokens)
    prompt_tokens     = int(agg.prompt_tokens)
    completion_tokens = int(agg.completion_tokens)
    avg_latency_ms    = float(agg.avg_latency_ms)
    escalation_count  = int(agg.escalation_count)

    # ── Distinct conversations (via message join) ──────────────────────────────
    conv_result = await session.execute(
        select(
            func.count(func.distinct(Message.conversation_id)).label("total")
        )
        .select_from(AgentMetric)
        .join(Message, AgentMetric.message_id == Message.id)
        .where(AgentMetric.created_at >= since)
    )
    total_conversations = int(conv_result.scalar() or 0)

    # ── Ticket stats ──────────────────────────────────────────────────────────
    ticket_result = await session.execute(
        select(Ticket).where(Ticket.created_at >= since)
    )
    tickets = ticket_result.scalars().all()

    total_tickets          = len(tickets)
    resolved_count         = sum(
        1 for t in tickets
        if t.status in (TicketStatus.resolved, TicketStatus.closed)
    )
    escalated_ticket_count = sum(
        1 for t in tickets if t.status == TicketStatus.escalated
    )
    csat_scores = [
        t.metadata_.get("survey_rating")
        for t in tickets
        if t.metadata_.get("survey_rating") is not None
    ]
    avg_csat = (
        round(sum(csat_scores) / len(csat_scores), 2) if csat_scores else None
    )

    # ── Cost ──────────────────────────────────────────────────────────────────
    estimated_cost_usd  = _estimate_cost(settings.openai_model, prompt_tokens, completion_tokens)
    cost_per_conv       = (
        estimated_cost_usd / total_conversations
        if total_conversations > 0 else 0.0
    )

    resolution_rate = (
        resolved_count / total_tickets * 100 if total_tickets > 0 else 0.0
    )
    escalation_rate = (
        escalation_count / total_runs * 100 if total_runs > 0 else 0.0
    )

    return {
        "time_range": time_range,
        "since": since.isoformat(),
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_tickets": total_tickets,
            "open_tickets": total_tickets - resolved_count,
            "avg_resolution_time_hours": round(avg_latency_ms / 60 / 1000, 2) if avg_latency_ms > 0 else 0,
            "avg_satisfaction_rating": avg_csat if avg_csat else 0,
            "sla_compliance_rate": round(100 - escalation_rate, 2) if escalation_rate > 0 else 100,
            "total_conversations_24h": total_conversations,
        },
        "tickets_by_status": {
            "open": 0,
            "in_progress": 0,
            "waiting_customer": 0,
            "resolved": resolved_count,
            "closed": 0,
        },
        "tickets_by_channel": {
            "web": 0,
            "gmail": 0,
            "whatsapp": 0,
        },
        "recent_tickets": [],
        "sla_breaches": [],
        "metrics_history": [],
    }


# ── log_agent_action ──────────────────────────────────────────────────────────

_action_logger = structlog.get_logger("agent.actions")


def log_agent_action(
    action: str,
    *,
    conversation_id: Optional[str] = None,
    message_id: Optional[str] = None,
    ticket_id: Optional[str] = None,
    channel: Optional[str] = None,
    **details: Any,
) -> None:
    """
    Emit a structured log event for a significant agent action.

    This is the single place where agent decisions, tool calls, and
    escalations are recorded in a machine-parseable format. The structlog
    contextvars (conversation_id, message_id, channel) bound by the worker
    are automatically merged in — you only need to pass extras.

    Args:
        action:          Short identifier, e.g. "ticket_created", "escalated",
                         "survey_sent", "guardrail_tripped", "resolved".
        conversation_id: Override context if calling outside the worker loop.
        message_id:      Override context if calling outside the worker loop.
        ticket_id:       Associated ticket UUID (string).
        channel:         "web" | "gmail" | "whatsapp".
        **details:       Any additional key-value pairs (reason, score, model…).

    Example:
        log_agent_action(
            "escalated",
            ticket_id=str(ticket.id),
            reason="customer sentiment score 0.72",
            auto=True,
        )
    """
    bound = _action_logger.bind(
        action=action,
        **{
            k: v
            for k, v in {
                "conversation_id": conversation_id,
                "message_id":      message_id,
                "ticket_id":       ticket_id,
                "channel":         channel,
            }.items()
            if v is not None
        },
        **details,
    )
    bound.info("agent_action")
