"""
Message ingestion service.

Orchestrates the full intake pipeline:
  1. Resolve or create customer
  2. Open or reuse a conversation
  3. Persist the inbound message
  4. Publish to Kafka for async agent processing
"""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import ChannelType, MessageDirection, MessageStatus
from app.repositories.conversations import ConversationRepository
from app.repositories.messages import MessageRepository
from app.services.customer_service import CustomerService
from app.services.kafka_producer import kafka_producer

logger = logging.getLogger(__name__)


class MessageService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._conversations = ConversationRepository(session)
        self._messages = MessageRepository(session)
        self._customers = CustomerService(session)

    async def ingest(
        self,
        *,
        channel: ChannelType,
        external_id: str,
        display_name: str,
        content: str,
        subject: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        company: str | None = None,
        raw_payload: dict | None = None,
    ) -> uuid.UUID:
        """
        Full intake pipeline. Returns the created Message ID.

        Steps:
          1. resolve_or_create customer
          2. find or open conversation
          3. persist Message with status=received
          4. publish to Kafka
        """
        raw_payload = raw_payload or {}

        # 1. Customer
        customer = await self._customers.resolve_or_create(
            channel=channel,
            external_id=external_id,
            display_name=display_name,
            email=email,
            phone=phone,
            company=company,
        )

        # 2. Conversation — reuse open one or start a new one
        conversation = await self._conversations.get_open_by_customer_and_channel(
            customer.id, channel
        )
        if conversation is None:
            conversation = await self._conversations.create(
                customer_id=customer.id,
                channel=channel,
                subject=subject or content[:120],
            )
            logger.info(
                "Opened new conversation %s for customer %s.",
                conversation.id,
                customer.id,
            )
        else:
            # Touch last_message_at
            from datetime import datetime, timezone
            await self._conversations.update(
                conversation,
                last_message_at=datetime.now(timezone.utc),
            )

        # 3. Persist message
        message = await self._messages.create(
            conversation_id=conversation.id,
            customer_id=customer.id,
            direction=MessageDirection.inbound,
            channel=channel,
            status=MessageStatus.received,
            content=content,
            raw_payload=raw_payload,
        )
        logger.info("Persisted message %s (channel=%s).", message.id, channel)

        # 4. Publish to Kafka
        await kafka_producer.publish_inbound_message(
            message_id=message.id,
            conversation_id=conversation.id,
            customer_id=customer.id,
            channel=channel.value,
            content=content,
            raw_payload=raw_payload,
        )

        return message.id
