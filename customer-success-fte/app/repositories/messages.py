"""Repository for the messages table."""

import uuid
from typing import Sequence

from sqlalchemy import select

from app.database import Message, MessageStatus
from app.repositories.base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    model = Message

    async def list_by_conversation(
        self,
        conversation_id: uuid.UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[Message]:
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.received_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def list_pending(self, *, limit: int = 50) -> Sequence[Message]:
        """Return messages in 'received' or 'processing' state for the worker."""
        result = await self.session.execute(
            select(Message)
            .where(
                Message.status.in_(
                    [MessageStatus.received, MessageStatus.processing]
                )
            )
            .order_by(Message.received_at.asc())
            .limit(limit)
        )
        return result.scalars().all()

    async def list_failed(self, *, limit: int = 50) -> Sequence[Message]:
        result = await self.session.execute(
            select(Message)
            .where(Message.status == MessageStatus.failed)
            .order_by(Message.received_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
