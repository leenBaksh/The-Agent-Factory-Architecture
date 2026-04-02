"""
Ticket lifecycle service.

Manages all ticket state transitions and the satisfaction survey workflow.

State machine
─────────────
  open → in_progress → waiting_customer → resolved → closed
                                                ↑
                                   (unhappy survey → reopen → open)

Survey workflow
───────────────
  1. Agent calls resolve_ticket tool → TicketLifecycleService.resolve_ticket()
  2. Service sends satisfaction survey email to the customer.
  3. Customer replies with a rating (1–5). The worker detects the reply
     via is_survey_response() and routes it to process_survey_response().
  4. Rating ≥ 4 → close ticket.
     Rating = 3 → close ticket (neutral).
     Rating ≤ 2 → reopen ticket + notify support team.
"""

import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import Ticket, TicketStatus
from app.repositories.customers import CustomerRepository
from app.repositories.tickets import TicketRepository
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)
settings = get_settings()


# ── Survey rating extraction ───────────────────────────────────────────────────

# Matches common survey reply patterns:
#   "Rating: 4"  |  "My rating is 4/5"  |  "4 out of 5"  |  "Survey: 3" | "5/5" | "★★★★★"
# Uses atomic grouping via possessive-like patterns to prevent ReDoS
_SURVEY_RATING_RE = re.compile(
    r"\b(?:rating|score|rated|satisfaction)[:\s]*([1-5])(?:\s*/\s*5)?\b"
    r"|\b([1-5])\s*/\s*5\b"
    r"|\b([1-5])\s+out\s+of\s+5\b"
    r"|\bsurvey[:\s]+([1-5])\b",
    re.IGNORECASE,
)

# Star rating pattern: ★★★★☆ (4 stars), ★★★★★ (5 stars), etc.
_STAR_RATING_RE = re.compile(r"([★☆]{3,5})")


def _extract_rating(content: str) -> Optional[int]:
    """
    Parse a satisfaction rating (1–5) from a message body.
    Supports numeric ratings (1-5), fractions (4/5), and star ratings (★★★★★).
    Returns None if no valid rating is found.
    """
    # First try numeric patterns
    match = _SURVEY_RATING_RE.search(content)
    if match:
        raw = next(g for g in match.groups() if g is not None)
        return int(raw)
    
    # Then try star ratings
    star_match = _STAR_RATING_RE.search(content)
    if star_match:
        stars = star_match.group(1)
        # Count filled stars (★) vs empty stars (☆)
        filled = stars.count("★")
        total = len(stars)
        if total >= 3:  # At least 3 stars to be considered a rating
            # Normalize to 1-5 scale
            return max(1, min(5, round(filled / total * 5)))
    
    return None


# ── Service ────────────────────────────────────────────────────────────────────


class TicketLifecycleService:
    """Manages ticket state transitions and the post-resolution survey flow."""

    # ── State transitions ─────────────────────────────────────────────────────

    async def start_working(
        self,
        ticket: Ticket,
        session: AsyncSession,
        agent_id: str = "ai",
    ) -> None:
        """Transition open → in_progress."""
        if ticket.status != TicketStatus.open:
            logger.debug(
                "start_working: ticket %s is %s — skipping.", ticket.id, ticket.status
            )
            return
        repo = TicketRepository(session)
        await repo.update(ticket, status=TicketStatus.in_progress, assigned_to=agent_id)
        logger.info("Ticket %s → in_progress (agent=%s)", ticket.id, agent_id)

    async def await_customer_reply(
        self,
        ticket: Ticket,
        session: AsyncSession,
    ) -> None:
        """Transition in_progress → waiting_customer."""
        repo = TicketRepository(session)
        await repo.update(ticket, status=TicketStatus.waiting_customer)
        logger.info("Ticket %s → waiting_customer", ticket.id)

    async def resolve_ticket(
        self,
        ticket: Ticket,
        session: AsyncSession,
        resolution: str,
        resolved_by: str = "ai",
    ) -> None:
        """
        Transition any active status → resolved.
        Sends a satisfaction survey to the customer as a side-effect.
        """
        if ticket.status in (TicketStatus.resolved, TicketStatus.closed):
            logger.debug(
                "Ticket %s is already %s — skipping resolve.",
                ticket.id,
                ticket.status,
            )
            return

        repo = TicketRepository(session)
        now = datetime.now(timezone.utc)
        await repo.update(
            ticket,
            status=TicketStatus.resolved,
            resolution=resolution,
            resolved_at=now,
            metadata_={
                **ticket.metadata_,
                "resolved_by": resolved_by,
                "resolved_at": now.isoformat(),
                "survey_sent": False,
            },
        )
        logger.info(
            "Ticket %s → resolved (by=%s resolution=%r)", ticket.id, resolved_by, resolution[:80]
        )

        # Send satisfaction survey — best-effort, never raises
        await self._send_satisfaction_survey(ticket=ticket, session=session)

    async def close_ticket(
        self,
        ticket: Ticket,
        session: AsyncSession,
    ) -> None:
        """Transition resolved → closed."""
        repo = TicketRepository(session)
        await repo.update(
            ticket,
            status=TicketStatus.closed,
            closed_at=datetime.now(timezone.utc),
        )
        logger.info("Ticket %s → closed", ticket.id)

    async def reopen_ticket(
        self,
        ticket: Ticket,
        session: AsyncSession,
        reason: str,
        customer_name: str = "",
    ) -> None:
        """
        Transition resolved/closed → open.
        Notifies the support team so they can follow up.
        """
        repo = TicketRepository(session)
        await repo.update(
            ticket,
            status=TicketStatus.open,
            resolved_at=None,
            closed_at=None,
            metadata_={
                **ticket.metadata_,
                "reopen_reason": reason,
                "reopened_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        logger.info("Ticket %s reopened. reason=%r", ticket.id, reason)

        await notification_service.notify_ticket_reopened(
            ticket_id=str(ticket.id),
            subject=ticket.subject,
            customer_name=customer_name,
            reason=reason,
        )

    # ── Survey workflow ───────────────────────────────────────────────────────

    async def _send_satisfaction_survey(
        self,
        ticket: Ticket,
        session: AsyncSession,
    ) -> None:
        """
        Look up the customer's email and dispatch a satisfaction survey.
        Failures are caught and logged — never propagated.
        """
        try:
            customer_repo = CustomerRepository(session)
            customer = await customer_repo.get(ticket.customer_id)

            if not customer or not customer.email:
                logger.debug(
                    "Survey skipped: no email for customer %s (ticket %s)",
                    ticket.customer_id,
                    ticket.id,
                )
                return

            await notification_service.send_satisfaction_survey(
                to_email=customer.email,
                customer_name=customer.display_name,
                ticket_id=str(ticket.id),
                subject=ticket.subject,
            )

            repo = TicketRepository(session)
            await repo.update(
                ticket,
                metadata_={
                    **ticket.metadata_,
                    "survey_sent": True,
                    "survey_sent_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            logger.info("Satisfaction survey sent: ticket=%s customer=%s", ticket.id, customer.email)

        except Exception as exc:
            logger.warning(
                "Failed to send satisfaction survey for ticket %s: %s", ticket.id, exc
            )

    async def process_survey_response(
        self,
        ticket: Ticket,
        session: AsyncSession,
        rating: int,
        feedback: str = "",
        customer_name: str = "",
    ) -> None:
        """
        Handle a customer's satisfaction survey response.

        Rating decision matrix:
          ≥ 4  →  close ticket  (satisfied)
          = 3  →  close ticket  (neutral — no action needed)
          ≤ 2  →  reopen ticket + notify support team  (dissatisfied)
        """
        repo = TicketRepository(session)
        await repo.update(
            ticket,
            metadata_={
                **ticket.metadata_,
                "survey_rating": rating,
                "survey_feedback": feedback[:500],
                "survey_responded_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        logger.info(
            "Survey response: ticket=%s rating=%d", ticket.id, rating
        )

        if rating <= 2:
            reason = (
                f"Customer rated satisfaction {rating}/5"
                + (f": {feedback[:200]}" if feedback else "")
            ).strip()
            await self.reopen_ticket(
                ticket=ticket,
                session=session,
                reason=reason,
                customer_name=customer_name,
            )
        else:
            await self.close_ticket(ticket=ticket, session=session)

    # ── Detection helpers ─────────────────────────────────────────────────────

    @staticmethod
    def is_survey_response(content: str) -> bool:
        """
        Return True if the message appears to be a satisfaction survey reply.
        Called by the worker before the main agent pipeline runs.
        """
        return _extract_rating(content) is not None

    @staticmethod
    def extract_rating(content: str) -> Optional[int]:
        """Extract the numeric rating (1–5) from a survey response message."""
        return _extract_rating(content)


# ── Module-level singleton ─────────────────────────────────────────────────────

ticket_lifecycle_service = TicketLifecycleService()
