"""
Kafka producer service.

Wraps aiokafka's AIOKafkaProducer with:
  - JSON serialisation
  - Typed publish methods per topic
  - Graceful start/stop for lifespan management
"""

import json
import logging
import uuid
from datetime import datetime, timezone

from aiokafka import AIOKafkaProducer

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _serialise(value: dict) -> bytes:
    return json.dumps(value, default=str).encode("utf-8")


class KafkaProducerService:
    def __init__(self) -> None:
        self._producer: AIOKafkaProducer | None = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def start(self) -> None:
        self._producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=_serialise,
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            acks="all",             # wait for all in-sync replicas
            enable_idempotence=True,
            compression_type="lz4",
        )
        await self._producer.start()
        logger.info("Kafka producer started.")

    async def stop(self) -> None:
        if self._producer:
            await self._producer.stop()
            logger.info("Kafka producer stopped.")

    # ── Publish helpers ───────────────────────────────────────────────────────

    async def _send(self, topic: str, key: str, payload: dict) -> None:
        if self._producer is None:
            raise RuntimeError("KafkaProducerService not started")
        await self._producer.send_and_wait(topic, value=payload, key=key)

    async def publish_inbound_message(
        self,
        *,
        message_id: uuid.UUID,
        conversation_id: uuid.UUID,
        customer_id: uuid.UUID,
        channel: str,
        content: str,
        raw_payload: dict,
    ) -> None:
        """Publish a new inbound message for the worker to process."""
        payload = {
            "event": "message.inbound",
            "message_id": str(message_id),
            "conversation_id": str(conversation_id),
            "customer_id": str(customer_id),
            "channel": channel,
            "content": content,
            "raw_payload": raw_payload,
            "published_at": datetime.now(timezone.utc).isoformat(),
        }
        await self._send(
            settings.kafka_topic_inbound,
            key=str(conversation_id),
            payload=payload,
        )
        logger.debug("Published inbound message %s to Kafka.", message_id)

    async def publish_escalation(
        self,
        *,
        ticket_id: uuid.UUID,
        conversation_id: uuid.UUID,
        customer_id: uuid.UUID,
        reason: str,
    ) -> None:
        """Publish an escalation event so human agents are notified."""
        payload = {
            "event": "ticket.escalated",
            "ticket_id": str(ticket_id),
            "conversation_id": str(conversation_id),
            "customer_id": str(customer_id),
            "reason": reason,
            "published_at": datetime.now(timezone.utc).isoformat(),
        }
        await self._send(
            settings.kafka_topic_escalations,
            key=str(ticket_id),
            payload=payload,
        )
        logger.info("Published escalation for ticket %s.", ticket_id)

    async def publish_outbound_response(
        self,
        *,
        outbound_message_id: uuid.UUID,
        inbound_message_id: uuid.UUID,
        conversation_id: uuid.UUID,
        customer_id: uuid.UUID,
        channel: str,
        content: str,
        customer_phone: str | None = None,
        customer_email: str | None = None,
        gmail_thread_id: str | None = None,
        was_escalated: bool = False,
    ) -> None:
        """Publish an outbound response for the response_handler to deliver."""
        payload = {
            "event": "message.outbound",
            "outbound_message_id": str(outbound_message_id),
            "inbound_message_id": str(inbound_message_id),
            "conversation_id": str(conversation_id),
            "customer_id": str(customer_id),
            "channel": channel,
            "content": content,
            "customer_phone": customer_phone,
            "customer_email": customer_email,
            "gmail_thread_id": gmail_thread_id,
            "was_escalated": was_escalated,
            "published_at": datetime.now(timezone.utc).isoformat(),
        }
        await self._send(
            settings.kafka_topic_outbound,
            key=str(conversation_id),
            payload=payload,
        )
        logger.debug("Published outbound response %s to Kafka.", outbound_message_id)

    async def publish_to_dlq(
        self,
        *,
        original_topic: str,
        original_payload: dict,
        error: str,
    ) -> None:
        """Publish an unprocessable message to the dead letter queue."""
        payload = {
            "event": "dlq.message",
            "original_topic": original_topic,
            "original_payload": original_payload,
            "error": error,
            "published_at": datetime.now(timezone.utc).isoformat(),
        }
        await self._send(settings.kafka_topic_dlq, key=None, payload=payload)
        logger.warning(
            "Message sent to DLQ (topic=%s): error=%s", original_topic, error
        )


# ── Module-level singleton (initialised in lifespan) ──────────────────────────
kafka_producer = KafkaProducerService()
