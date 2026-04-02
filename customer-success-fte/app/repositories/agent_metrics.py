"""Repository for the agent_metrics table."""

import uuid
from typing import Sequence

from sqlalchemy import func, select

from app.database import AgentMetric
from app.repositories.base import BaseRepository


class AgentMetricRepository(BaseRepository[AgentMetric]):
    model = AgentMetric

    async def list_by_message(self, message_id: uuid.UUID) -> Sequence[AgentMetric]:
        result = await self.session.execute(
            select(AgentMetric)
            .where(AgentMetric.message_id == message_id)
            .order_by(AgentMetric.created_at.asc())
        )
        return result.scalars().all()

    async def list_by_ticket(self, ticket_id: uuid.UUID) -> Sequence[AgentMetric]:
        result = await self.session.execute(
            select(AgentMetric)
            .where(AgentMetric.ticket_id == ticket_id)
            .order_by(AgentMetric.created_at.asc())
        )
        return result.scalars().all()

    async def total_tokens_by_model(self) -> list[dict]:
        """Aggregate total token usage grouped by model name."""
        result = await self.session.execute(
            select(
                AgentMetric.model,
                func.sum(AgentMetric.total_tokens).label("total_tokens"),
                func.count(AgentMetric.id).label("calls"),
            ).group_by(AgentMetric.model)
        )
        return [
            {"model": row.model, "total_tokens": row.total_tokens, "calls": row.calls}
            for row in result.all()
        ]

    async def escalation_rate(self) -> float:
        """Return the fraction of processed messages that were escalated."""
        total = await self.session.scalar(select(func.count(AgentMetric.id)))
        if not total:
            return 0.0
        escalated = await self.session.scalar(
            select(func.count(AgentMetric.id)).where(
                AgentMetric.was_escalated.is_(True)
            )
        )
        return (escalated or 0) / total
