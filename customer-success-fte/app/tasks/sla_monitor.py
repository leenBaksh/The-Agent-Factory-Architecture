"""
SLA monitor — long-running background asyncio task.

Started in the FastAPI lifespan and cancelled on shutdown.

Every `sla_monitor_interval_minutes` the monitor:
  1. Queries for open/in-progress tickets older than `escalation_sla_hours`.
  2. Escalates each breached ticket (idempotent — already-escalated skip).
  3. Notifies the support team via email and/or Slack.
"""

import asyncio
import logging
from datetime import datetime, timezone

from app.config import get_settings
from app.database import AsyncSessionFactory
from app.repositories.customers import CustomerRepository
from app.services.escalation_service import escalation_service
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)
settings = get_settings()


async def _check_sla_once() -> None:
    """Single SLA scan — runs in its own DB session, commits on success."""
    async with AsyncSessionFactory() as session:
        breached = await escalation_service.find_sla_breached_tickets(session)

        if not breached:
            logger.debug("SLA monitor: no breached tickets found.")
            return

        logger.info("SLA monitor: %d breached ticket(s) found.", len(breached))
        customer_repo = CustomerRepository(session)

        for ticket in breached:
            reason = (
                f"Ticket has been open for more than {settings.escalation_sla_hours} hours "
                f"without resolution"
            )
            try:
                await escalation_service.escalate(
                    ticket=ticket,
                    reason=reason,
                    session=session,
                )

                customer = await customer_repo.get(ticket.customer_id)
                customer_name = customer.display_name if customer else "Unknown"

                hours_open = (
                    datetime.now(timezone.utc) - ticket.created_at
                ).total_seconds() / 3600

                priority = (
                    ticket.priority.value
                    if hasattr(ticket.priority, "value")
                    else str(ticket.priority)
                )

                await notification_service.notify_sla_breach(
                    ticket_id=str(ticket.id),
                    subject=ticket.subject,
                    customer_name=customer_name,
                    hours_open=hours_open,
                    priority=priority,
                )

            except Exception as exc:
                logger.error(
                    "SLA monitor: failed to process ticket %s: %s",
                    ticket.id,
                    exc,
                    exc_info=True,
                )

        await session.commit()


async def run_sla_monitor() -> None:
    """
    Long-running coroutine that sleeps between SLA scans.

    Handles asyncio.CancelledError cleanly so it can be stopped via task.cancel().
    Unexpected errors are logged but do not kill the loop — the monitor recovers
    automatically on the next iteration.
    """
    interval_s = settings.sla_monitor_interval_minutes * 60
    logger.info(
        "SLA monitor started — check interval=%dm, SLA threshold=%dh",
        settings.sla_monitor_interval_minutes,
        settings.escalation_sla_hours,
    )

    while True:
        try:
            await _check_sla_once()
        except asyncio.CancelledError:
            logger.info("SLA monitor cancelled.")
            raise
        except Exception as exc:
            logger.error(
                "SLA monitor scan failed: %s", exc, exc_info=True
            )

        try:
            await asyncio.sleep(interval_s)
        except asyncio.CancelledError:
            logger.info("SLA monitor cancelled during sleep.")
            raise
