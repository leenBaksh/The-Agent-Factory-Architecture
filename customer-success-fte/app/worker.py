"""
Kafka inbound message worker.

Consumes from kafka_topic_inbound (cs-fte.messages.inbound — the "incoming.support"
topic in logical terms), runs each message through the OpenAI Agents SDK, then
publishes the agent's response to kafka_topic_outbound for the response handler.

Run as a standalone process:
    python -m app.worker

Guarantees:
  - At-least-once delivery: offsets committed only after full processing.
  - Poison-pill protection: after _MAX_RETRIES failures, the message is
    forwarded to the DLQ topic (cs-fte.messages.dlq) and the offset is committed
    so the consumer does not get stuck.
  - Graceful shutdown: SIGTERM / SIGINT trigger a clean stop.
"""

import asyncio
import json
import logging
import platform
import signal
import uuid
from datetime import datetime, timezone

import structlog
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError
from sqlalchemy import select

from app.agents.coordinator import AgentResult, run_support_agent
from app.agents.tools import AgentContext
from app.config import get_settings
from app.database import AsyncSessionFactory, MessageStatus, Ticket, TicketStatus
from app.repositories.customers import CustomerRepository
from app.repositories.messages import MessageRepository
from app.services.kafka_producer import kafka_producer
from app.services.metrics_service import update_metrics
from app.services.ticket_service import TicketLifecycleService, ticket_lifecycle_service

logger = logging.getLogger(__name__)
settings = get_settings()

_MAX_RETRIES = 3
_RETRY_BACKOFF_BASE_S = 2          # seconds; doubles each attempt (2, 4, 8)


# ── Worker class ───────────────────────────────────────────────────────────────


class SupportWorker:
    """
    Kafka consumer that processes inbound support messages through the agent.

    One worker instance = one consumer in the consumer group.
    Scale horizontally by running multiple worker processes; Kafka will
    distribute partitions across them automatically.
    """

    def __init__(self) -> None:
        self._consumer: AIOKafkaConsumer | None = None
        self._running: bool = False

    async def start(self) -> None:
        self._consumer = AIOKafkaConsumer(
            settings.kafka_topic_inbound,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id=settings.kafka_consumer_group,
            enable_auto_commit=False,       # manual commit after processing
            auto_offset_reset="earliest",
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            session_timeout_ms=45_000,
            heartbeat_interval_ms=15_000,
            max_poll_records=5,             # keep each poll batch small
            max_poll_interval_ms=300_000,   # 5 min max per batch (agent is slow)
        )
        await self._consumer.start()
        self._running = True
        logger.info(
            "Worker started | topic=%s group=%s",
            settings.kafka_topic_inbound,
            settings.kafka_consumer_group,
        )

    async def stop(self) -> None:
        self._running = False
        if self._consumer:
            await self._consumer.stop()
            logger.info("Worker stopped.")

    async def run(self) -> None:
        """Main loop — consumes and processes messages until stopped."""
        await self.start()
        try:
            async for kafka_msg in self._consumer:
                if not self._running:
                    break
                await self._process_with_retry(kafka_msg)
        finally:
            await self.stop()

    # ── Retry wrapper ──────────────────────────────────────────────────────────

    async def _process_with_retry(self, kafka_msg) -> None:
        """
        Process one Kafka message with exponential-backoff retries.

        Survey responses are detected and routed before the agent pipeline runs.
        On permanent failure (all retries exhausted):
          1. Publish to DLQ.
          2. Commit the offset so the consumer advances past the poison message.
        """
        payload: dict = kafka_msg.value
        message_id_str: str = payload.get("message_id", "unknown")

        # Bind request-scoped context — all log lines below automatically include these
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            message_id=message_id_str,
            conversation_id=payload.get("conversation_id", ""),
            channel=payload.get("channel", ""),
        )

        # ── Survey response short-circuit ──────────────────────────────────────
        if await self._check_and_process_survey(payload):
            logger.info(
                "Survey response handled — skipping agent: message_id=%s",
                message_id_str,
            )
        else:
            for attempt in range(_MAX_RETRIES):
                try:
                    await self._process_message(payload)
                    break  # success — exit retry loop

                except Exception as exc:
                    if attempt < _MAX_RETRIES - 1:
                        wait_s = _RETRY_BACKOFF_BASE_S ** attempt
                        logger.warning(
                            "Attempt %d/%d failed for message_id=%s: %s. "
                            "Retrying in %ds.",
                            attempt + 1,
                            _MAX_RETRIES,
                            message_id_str,
                            exc,
                            wait_s,
                        )
                        await asyncio.sleep(wait_s)
                    else:
                        logger.error(
                            "All %d attempts failed for message_id=%s. "
                            "Forwarding to DLQ. Error: %s",
                            _MAX_RETRIES,
                            message_id_str,
                            exc,
                            exc_info=True,
                        )
                        await self._send_to_dlq(payload, str(exc))

        # Always commit — advance past this message regardless of outcome
        try:
            await self._consumer.commit()
        except KafkaError as exc:
            logger.error("Failed to commit Kafka offset: %s", exc)

    # ── Core processing pipeline ───────────────────────────────────────────────

    async def _process_message(self, payload: dict) -> None:
        """
        Full processing pipeline for one inbound Kafka message.

        Steps:
          a) Validate the payload and resolve the message record in the DB.
          b) Update message status → processing.
          c) Load customer context (email, phone).
          d) Build AgentContext.
          e) Run the OpenAI Agents SDK (run_support_agent).
          f) Publish outbound response to Kafka (for response_handler).
          g) Update message status → replied | failed.
          h) Commit the DB transaction.
        """
        # ── a) Validate payload ────────────────────────────────────────────────
        message_id_str = payload.get("message_id", "")
        if not message_id_str:
            logger.warning("Kafka payload missing message_id — skipping.")
            return

        try:
            message_id = uuid.UUID(message_id_str)
        except ValueError:
            logger.warning("Invalid message_id UUID %r — skipping.", message_id_str)
            return

        channel = payload.get("channel", "")
        content = payload.get("content", "")

        logger.info(
            "Processing message: id=%s channel=%s", message_id, channel
        )

        async with AsyncSessionFactory() as session:
            msg_repo = MessageRepository(session)

            # ── b) Load message record ─────────────────────────────────────────
            message = await msg_repo.get(message_id)
            if message is None:
                logger.warning(
                    "Message %s not found in DB — possibly deleted. Skipping.",
                    message_id,
                )
                return

            # Skip if already processed (idempotency guard)
            if message.status == MessageStatus.replied:
                logger.info(
                    "Message %s already replied — skipping duplicate.", message_id
                )
                return

            # Skip if currently processing and not stuck (crash recovery)
            if message.status == MessageStatus.processing:
                processed_at = message.processing_metadata.get("processed_at") if message.processing_metadata else None
                if processed_at:
                    try:
                        processing_start = datetime.fromisoformat(processed_at.replace("Z", "+00:00"))
                        time_in_processing = (datetime.now(timezone.utc) - processing_start).total_seconds()
                        # If processing for more than 5 minutes, consider it stuck and reprocess
                        if time_in_processing < 300:  # 5 minutes
                            logger.info(
                                "Message %s still processing (started %d seconds ago) — skipping.",
                                message_id,
                                int(time_in_processing),
                            )
                            return
                        else:
                            logger.warning(
                                "Message %s stuck in processing for %d seconds — reprocessing.",
                                message_id,
                                int(time_in_processing),
                            )
                    except (ValueError, TypeError):
                        logger.warning(
                            "Message %s has invalid processed_at timestamp — reprocessing.",
                            message_id,
                        )
                else:
                    logger.warning(
                        "Message %s in processing status but no timestamp — reprocessing.",
                        message_id,
                    )

            # ── c) Update to 'processing' with timestamp ───────────────────────
            processing_metadata = {
                **message.processing_metadata,
                "processed_at": datetime.now(timezone.utc).isoformat(),
            }
            await msg_repo.update(message, status=MessageStatus.processing, processing_metadata=processing_metadata)
            await session.flush()

            # ── d) Load customer ───────────────────────────────────────────────
            customer_repo = CustomerRepository(session)
            customer = await customer_repo.get(message.customer_id)

            # ── e) Build AgentContext ──────────────────────────────────────────
            context = AgentContext(
                session=session,
                message_id=message.id,
                conversation_id=message.conversation_id,
                customer_id=message.customer_id,
                channel=channel or message.channel.value,
                customer_email=customer.email if customer else None,
                customer_phone=customer.phone if customer else None,
            )

            # ── f) Run the agent ───────────────────────────────────────────────
            result: AgentResult = await run_support_agent(
                context=context,
                content=content or message.content,
            )

            # ── g) Handle result ───────────────────────────────────────────────
            if result.success:
                logger.info(
                    "Agent run succeeded: message_id=%s escalated=%s latency_ms=%d",
                    message_id,
                    result.escalated,
                    result.latency_ms,
                )

                # Publish to outbound topic so response_handler can deliver
                if context.outbound_messages_created:
                    outbound_id = context.outbound_messages_created[-1]
                    gmail_thread_id = (
                        message.raw_payload.get("thread_id")
                        or message.raw_payload.get("gmail_id")
                    )
                    await kafka_producer.publish_outbound_response(
                        outbound_message_id=outbound_id,
                        inbound_message_id=message_id,
                        conversation_id=message.conversation_id,
                        customer_id=message.customer_id,
                        channel=context.channel,
                        content=result.final_output or "",
                        customer_phone=context.customer_phone,
                        customer_email=context.customer_email,
                        gmail_thread_id=gmail_thread_id,
                        was_escalated=result.escalated,
                    )
                    logger.debug(
                        "Outbound response published: outbound_id=%s", outbound_id
                    )
                else:
                    logger.warning(
                        "Agent completed but no outbound message was created "
                        "(message_id=%s). Agent may not have called send_response.",
                        message_id,
                    )

                # Sync message status if not already set to 'replied' by the tool
                if message.status != MessageStatus.replied:
                    await msg_repo.update(
                        message,
                        status=MessageStatus.replied,
                        processing_metadata={
                            **message.processing_metadata,
                            "agent_latency_ms": result.latency_ms,
                            "escalated": result.escalated,
                            "processed_at": datetime.now(timezone.utc).isoformat(),
                        },
                    )

            else:
                # Agent run failed — mark message as failed
                logger.error(
                    "Agent run failed: message_id=%s error=%s",
                    message_id,
                    result.error,
                )
                await msg_repo.update(
                    message,
                    status=MessageStatus.failed,
                    error_details={
                        "error": result.error,
                        "latency_ms": result.latency_ms,
                    },
                    processing_metadata={
                        **message.processing_metadata,
                        "agent_latency_ms": result.latency_ms,
                        "failed_at": datetime.now(timezone.utc).isoformat(),
                    },
                )

            # ── h) Aggregate conversation metrics (best-effort) ───────────────
            if result.success:
                await update_metrics(
                    conversation_id=message.conversation_id,
                    session=session,
                )

            # ── i) Commit DB transaction ───────────────────────────────────────
            await session.commit()

    # ── Survey detection ────────────────────────────────────────────────────────

    async def _check_and_process_survey(self, payload: dict) -> bool:
        """
        Detect satisfaction survey responses and process them without the agent.

        Strategy:
          1. Check if message content looks like a survey reply (rating pattern).
          2. Find the most recently resolved ticket for this customer that had a
             survey sent.
          3. Call TicketLifecycleService.process_survey_response().

        Returns True if the message was a survey response and was handled,
        so the caller can skip the main agent pipeline entirely.
        """
        content = payload.get("content", "")
        if not TicketLifecycleService.is_survey_response(content):
            return False

        rating = TicketLifecycleService.extract_rating(content)
        if rating is None:
            return False

        customer_id_str = payload.get("customer_id", "")
        if not customer_id_str:
            return False

        try:
            customer_id = uuid.UUID(customer_id_str)
        except ValueError:
            return False

        async with AsyncSessionFactory() as session:
            # Find the most recent resolved ticket for this customer
            # that had a survey dispatched
            result = await session.execute(
                select(Ticket)
                .where(
                    Ticket.customer_id == customer_id,
                    Ticket.status == TicketStatus.resolved,
                )
                .order_by(Ticket.resolved_at.desc())
                .limit(5)
            )
            candidates = result.scalars().all()

            # Prefer tickets where survey_sent=True; fall back to any resolved ticket
            ticket = next(
                (t for t in candidates if t.metadata_.get("survey_sent")),
                candidates[0] if candidates else None,
            )

            if not ticket:
                logger.debug(
                    "Survey response detected but no resolved ticket found "
                    "for customer %s — routing to agent instead.",
                    customer_id,
                )
                return False

            customer_repo = CustomerRepository(session)
            customer = await customer_repo.get(customer_id)
            customer_name = customer.display_name if customer else ""

            try:
                await ticket_lifecycle_service.process_survey_response(
                    ticket=ticket,
                    session=session,
                    rating=rating,
                    feedback=content,
                    customer_name=customer_name,
                )
                await session.commit()
                logger.info(
                    "Survey processed: ticket=%s rating=%d customer=%s",
                    ticket.id,
                    rating,
                    customer_id,
                )
                return True
            except Exception as exc:
                logger.error(
                    "Failed to process survey response for ticket %s: %s",
                    ticket.id,
                    exc,
                    exc_info=True,
                )
                # On survey processing failure, fall through to the agent
                return False

    # ── DLQ helper ─────────────────────────────────────────────────────────────

    async def _send_to_dlq(self, payload: dict, error: str) -> None:
        """Forward an unprocessable message to the dead letter queue."""
        try:
            await kafka_producer.publish_to_dlq(
                original_topic=settings.kafka_topic_inbound,
                original_payload=payload,
                error=error,
            )
        except Exception as exc:
            # DLQ failure is catastrophic — log at CRITICAL but don't crash
            logger.critical(
                "FAILED to publish to DLQ! message_id=%s dlq_error=%s",
                payload.get("message_id"),
                exc,
            )


# ── Standalone entry point ─────────────────────────────────────────────────────


async def main() -> None:
    from app.logging_config import configure_logging
    configure_logging()
    logger.info("Starting Support Worker …")

    await kafka_producer.start()

    worker = SupportWorker()
    loop = asyncio.get_event_loop()

    def _shutdown() -> None:
        logger.info("Shutdown signal received — stopping worker.")
        asyncio.create_task(worker.stop())

    # Signal handlers only work on Unix (Linux/macOS)
    # On Windows, use Ctrl+C to stop the process
    if platform.system() != "Windows":
        loop.add_signal_handler(signal.SIGTERM, _shutdown)
        loop.add_signal_handler(signal.SIGINT, _shutdown)

    try:
        await worker.run()
    finally:
        await kafka_producer.stop()
        logger.info("Worker process exited cleanly.")


if __name__ == "__main__":
    asyncio.run(main())
