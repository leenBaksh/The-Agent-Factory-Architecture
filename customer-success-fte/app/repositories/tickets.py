"""Repository for the tickets table."""

import uuid
from typing import Sequence

from sqlalchemy import select

from app.database import Ticket, TicketPriority, TicketStatus
from app.repositories.base import BaseRepository


class TicketRepository(BaseRepository[Ticket]):
    model = Ticket

    async def list_by_customer(
        self,
        customer_id: uuid.UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[Ticket]:
        result = await self.session.execute(
            select(Ticket)
            .where(Ticket.customer_id == customer_id)
            .order_by(Ticket.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def list_by_status(
        self,
        status: TicketStatus,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[Ticket]:
        result = await self.session.execute(
            select(Ticket)
            .where(Ticket.status == status)
            .order_by(Ticket.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def list_escalated(self, *, limit: int = 100) -> Sequence[Ticket]:
        result = await self.session.execute(
            select(Ticket)
            .where(Ticket.status == TicketStatus.escalated)
            .order_by(Ticket.escalated_at.asc())
            .limit(limit)
        )
        return result.scalars().all()

    async def list_by_conversation(
        self, conversation_id: uuid.UUID
    ) -> Sequence[Ticket]:
        result = await self.session.execute(
            select(Ticket)
            .where(Ticket.conversation_id == conversation_id)
            .order_by(Ticket.created_at.desc())
        )
        return result.scalars().all()

    async def list_by_priority(
        self,
        priority: TicketPriority,
        *,
        limit: int = 100,
    ) -> Sequence[Ticket]:
        result = await self.session.execute(
            select(Ticket)
            .where(Ticket.priority == priority)
            .order_by(Ticket.created_at.asc())
            .limit(limit)
        )
        return result.scalars().all()
