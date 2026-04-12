"""
Stub Kafka producer for development without Kafka.
Allows the application to start when aiokafka is not installed.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class StubKafkaProducer:
    """No-op Kafka producer for development"""
    
    def __init__(self):
        self.started = False
    
    async def start(self):
        """No-op start"""
        self.started = True
        logger.debug("Stub Kafka producer started (no-op)")
    
    async def stop(self):
        """No-op stop"""
        self.started = False
        logger.debug("Stub Kafka producer stopped")
    
    async def send(self, topic: str, value: Any = None, key: Any = None):
        """No-op send - just logs"""
        logger.debug(f"Stub Kafka send to {topic} (no-op): {value}")
    
    async def send_and_wait(self, topic: str, value: Any = None, key: Any = None):
        """No-op send_and_wait"""
        logger.debug(f"Stub Kafka send_and_wait to {topic} (no-op): {value}")


# Module-level singleton
kafka_producer = StubKafkaProducer()
