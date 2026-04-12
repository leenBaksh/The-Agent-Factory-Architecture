"""
Kafka producer service.

Wraps aiokafka's AIOKafkaProducer with:
  - JSON serialisation
  - Typed publish methods per topic
  - Graceful start/stop for lifespan management

If aiokafka is not installed, provides a no-op stub.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Try to import aiokafka
try:
    from aiokafka import AIOKafkaProducer
    AIOKAFKA_AVAILABLE = True
except ImportError:
    AIOKAFKA_AVAILABLE = False
    AIOKafkaProducer = None
    logger.warning("aiokafka not installed - using stub Kafka producer")

from app.config import get_settings

settings = get_settings()


def _serialise(value: dict) -> bytes:
    import json
    return json.dumps(value, default=str).encode("utf-8")


if AIOKAFKA_AVAILABLE:
    # Real Kafka implementation
    class KafkaProducerService:
        def __init__(self) -> None:
            self._producer: Optional[AIOKafkaProducer] = None

        async def start(self) -> None:
            if self._producer is None:
                self._producer = AIOKafkaProducer(
                    bootstrap_servers=settings.kafka_bootstrap_servers,
                    value_serializer=_serialise,
                )
                await self._producer.start()
                logger.info("Kafka producer connected")

        async def stop(self) -> None:
            if self._producer:
                await self._producer.stop()
                self._producer = None
                logger.info("Kafka producer stopped")

        async def send(self, topic: str, value: dict) -> None:
            if not self._producer:
                raise RuntimeError("Kafka producer not started")
            await self._producer.send_and_wait(topic, value=value)
            logger.debug(f"Published to {topic}")

        async def send_message(self, message: dict) -> None:
            await self.send(settings.kafka_topic_outbound, message)

        async def send_escalation(self, ticket: dict) -> None:
            await self.send(settings.kafka_topic_escalations, ticket)

        async def send_to_dlq(self, message: dict, error: str) -> None:
            message["_dlq_error"] = error
            await self.send(settings.kafka_topic_dlq, message)
            logger.warning(f"Message sent to DLQ: {error}")

    kafka_producer = KafkaProducerService()

else:
    # Stub implementation for development
    class KafkaProducerService:
        """Stub Kafka producer for development without aiokafka"""
        def __init__(self) -> None:
            self.started = False

        async def start(self) -> None:
            self.started = True
            logger.info("Stub Kafka producer started (no-op - install aiokafka for real Kafka)")

        async def stop(self) -> None:
            self.started = False
            logger.info("Stub Kafka producer stopped")

        async def send(self, topic: str, value: dict) -> None:
            logger.debug(f"Stub Kafka publish to {topic} (no-op)")

        async def send_message(self, message: dict) -> None:
            await self.send(settings.kafka_topic_outbound, message)

        async def send_escalation(self, ticket: dict) -> None:
            await self.send(settings.kafka_topic_escalations, ticket)

        async def send_to_dlq(self, message: dict, error: str) -> None:
            logger.warning(f"Stub DLQ (no-op): {error}")

    kafka_producer = KafkaProducerService()
