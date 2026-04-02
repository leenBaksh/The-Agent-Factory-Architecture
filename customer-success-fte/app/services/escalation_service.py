"""
Escalation service.

Evaluates inbound messages and open tickets against 4 escalation rules.
On a rule match, transitions the ticket to 'escalated' status and publishes
a Kafka event so the notification service can alert the team.

Escalation rules
────────────────
  1. ConfidenceRule  — agent confidence score < threshold (default 0.70)
  2. KeywordRule     — message contains sensitive keywords (refund, lawsuit …)
  3. SentimentRule   — customer anger score ≥ threshold (0.60)
  4. SLABreachRule   — ticket has been open for > escalation_sla_hours hours
"""

from __future__ import annotations

import abc
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import Ticket, TicketStatus
from app.repositories.tickets import TicketRepository
from app.services.kafka_producer import kafka_producer

logger = logging.getLogger(__name__)
settings = get_settings()


# ── Escalation reason dataclass ────────────────────────────────────────────────


@dataclass
class EscalationReason:
    rule: str
    detail: str


# ── Abstract rule base ─────────────────────────────────────────────────────────


class EscalationRule(abc.ABC):
    """Base class for all escalation rules."""

    @abc.abstractmethod
    def evaluate(
        self,
        content: str,
        confidence_score: Optional[float] = None,
        sentiment_score: Optional[float] = None,
    ) -> Optional[EscalationReason]:
        """Return an EscalationReason if the rule triggers, else None."""


# ── Concrete rules ─────────────────────────────────────────────────────────────


class ConfidenceRule(EscalationRule):
    """Escalate if the agent's confidence score is below threshold."""

    def __init__(self, threshold: float = 0.70) -> None:
        self._threshold = threshold

    def evaluate(
        self,
        content: str,
        confidence_score: Optional[float] = None,
        sentiment_score: Optional[float] = None,
    ) -> Optional[EscalationReason]:
        if confidence_score is not None and confidence_score < self._threshold:
            return EscalationReason(
                rule="confidence",
                detail=(
                    f"Agent confidence {confidence_score:.2f} is below "
                    f"threshold {self._threshold:.2f}"
                ),
            )
        return None


_ESCALATION_KEYWORDS: frozenset[str] = frozenset(
    {
        "refund",
        "lawsuit",
        "legal",
        "lawyer",
        "attorney",
        "sue",
        "court",
        "chargeback",
        "fraud",
        "scam",
        "stolen",
        "data breach",
        "gdpr",
        "hipaa",
        "compliance",
        "regulator",
        "ombudsman",
        "arbitration",
    }
)


class KeywordRule(EscalationRule):
    """Escalate if the message contains a high-risk keyword."""

    def evaluate(
        self,
        content: str,
        confidence_score: Optional[float] = None,
        sentiment_score: Optional[float] = None,
    ) -> Optional[EscalationReason]:
        lower = content.lower()
        for keyword in _ESCALATION_KEYWORDS:
            if keyword in lower:
                return EscalationReason(
                    rule="keyword",
                    detail=f"Message contains escalation keyword: '{keyword}'",
                )
        return None


class SentimentRule(EscalationRule):
    """Escalate if the customer anger sentiment score meets or exceeds threshold."""

    def __init__(self, threshold: float = 0.60) -> None:
        self._threshold = threshold

    def evaluate(
        self,
        content: str,
        confidence_score: Optional[float] = None,
        sentiment_score: Optional[float] = None,
    ) -> Optional[EscalationReason]:
        if sentiment_score is not None and sentiment_score >= self._threshold:
            return EscalationReason(
                rule="sentiment",
                detail=(
                    f"Customer anger score {sentiment_score:.2f} "
                    f">= threshold {self._threshold:.2f}"
                ),
            )
        return None


# ── Escalation service ─────────────────────────────────────────────────────────


class EscalationService:
    """
    Evaluates messages against all escalation rules and acts on matches.

    Rules are evaluated in order: ConfidenceRule → KeywordRule → SentimentRule.
    All matching rules are returned; the caller decides how many to act on.

    SLA breach detection is a separate DB scan (find_sla_breached_tickets).
    """

    def __init__(self) -> None:
        self._rules: list[EscalationRule] = [
            ConfidenceRule(
                threshold=settings.auto_escalation_confidence_threshold
            ),
            KeywordRule(),
            SentimentRule(threshold=0.60),
        ]

    def evaluate(
        self,
        content: str,
        confidence_score: Optional[float] = None,
        sentiment_score: Optional[float] = None,
    ) -> list[EscalationReason]:
        """
        Run all rules against the given inputs and return every triggered reason.
        An empty list means no escalation is needed.
        """
        reasons: list[EscalationReason] = []
        for rule in self._rules:
            reason = rule.evaluate(
                content=content,
                confidence_score=confidence_score,
                sentiment_score=sentiment_score,
            )
            if reason:
                reasons.append(reason)
        return reasons

    async def escalate(
        self,
        ticket: Ticket,
        reason: str,
        session: AsyncSession,
    ) -> None:
        """
        Transition a ticket to 'escalated' and publish a Kafka event.
        Idempotent — tickets already in 'escalated' status are skipped.
        """
        if ticket.status == TicketStatus.escalated:
            logger.debug(
                "Ticket %s is already escalated — skipping.", ticket.id
            )
            return

        repo = TicketRepository(session)
        await repo.update(
            ticket,
            status=TicketStatus.escalated,
            assigned_to="human",
            escalated_at=datetime.now(timezone.utc),
            metadata_={
                **ticket.metadata_,
                "escalation_reason": reason,
                "auto_escalated": True,
                "escalated_by": "sla_monitor",
            },
        )

        await kafka_producer.publish_escalation(
            ticket_id=ticket.id,
            conversation_id=ticket.conversation_id,
            customer_id=ticket.customer_id,
            reason=reason,
        )

        logger.info(
            "Ticket escalated: ticket_id=%s reason=%r", ticket.id, reason
        )

    async def find_sla_breached_tickets(
        self, session: AsyncSession
    ) -> list[Ticket]:
        """
        Return open or in-progress tickets whose age exceeds escalation_sla_hours.
        Excludes tickets that are already escalated, resolved, or closed.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(
            hours=settings.escalation_sla_hours
        )
        result = await session.execute(
            select(Ticket).where(
                Ticket.status.in_(
                    [TicketStatus.open, TicketStatus.in_progress]
                ),
                Ticket.created_at < cutoff,
            )
        )
        return list(result.scalars().all())


# ── Module-level singleton ─────────────────────────────────────────────────────

escalation_service = EscalationService()
