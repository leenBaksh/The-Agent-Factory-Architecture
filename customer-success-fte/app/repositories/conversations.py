"""Repository for the conversations table."""

import uuid
from typing import Sequence

from sqlalchemy import select

from app.database import ChannelType, Conversation, TicketStatus
from app.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    model = Conversation

    async def get_open_by_customer_and_channel(
        self,
        customer_id: uuid.UUID,
        channel: ChannelType,
    ) -> Conversation | None:
        """Return the most recent open conversation for a customer+channel pair."""
        result = await self.session.execute(
            select(Conversation)
            .where(
                Conversation.customer_id == customer_id,
                Conversation.channel == channel,
                Conversation.status == TicketStatus.open,
            )
            .order_by(Conversation.last_message_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_by_customer(
        self,
        customer_id: uuid.UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[Conversation]:
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.customer_id == customer_id)
            .order_by(Conversation.last_message_at.desc())
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
    ) -> Sequence[Conversation]:
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.status == status)
            .order_by(Conversation.last_message_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
