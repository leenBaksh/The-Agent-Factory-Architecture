"""
Kafka outbound response handler.

Consumes from kafka_topic_outbound (cs-fte.messages.outbound — the "outgoing.responses"
topic in logical terms) and delivers the agent's reply to the correct channel:

  - WhatsApp : verify delivery; retry via Meta Cloud API if tool delivery failed.
  - Gmail    : send reply email via Gmail API (in-thread) OR SMTP.
  - Web      : update ticket status; response already in DB for frontend polling.

Run as a standalone process:
    python -m app.response_handler

Uses a SEPARATE consumer group so it runs independently from the worker.
Manual offset commits ensure at-least-once delivery.
"""

import asyncio
import email.mime.multipart
import email.mime.text
import json
import logging
import signal
import uuid
from datetime import datetime, timezone

import aiosmtplib
import httpx
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError

from app.config import get_settings
from app.database import AsyncSessionFactory, MessageStatus, TicketStatus
from app.repositories.messages import MessageRepository
from app.repositories.tickets import TicketRepository
from app.services.gmail_service import gmail_service

logger = logging.getLogger(__name__)
settings = get_settings()

_RESPONSE_GROUP = f"{settings.kafka_consumer_group}-response-handler"
_MAX_RETRIES = 2
_RETRY_BACKOFF_BASE_S = 3         # seconds (3, 9 for attempts 0 and 1)


# ── Handler class ──────────────────────────────────────────────────────────────


class ResponseHandler:
    """
    Kafka consumer that delivers agent responses to their destination channel.

    Designed to run alongside (not inside) the FastAPI process.
    Scale independently from the worker — delivery is I/O bound (HTTP, SMTP).
    """

    def __init__(self) -> None:
        self._consumer: AIOKafkaConsumer | None = None
        self._running: bool = False

    async def start(self) -> None:
        self._consumer = AIOKafkaConsumer(
            settings.kafka_topic_outbound,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id=_RESPONSE_GROUP,
            enable_auto_commit=False,
            auto_offset_reset="earliest",
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            session_timeout_ms=30_000,
            heartbeat_interval_ms=10_000,
            max_poll_records=20,
        )
        await self._consumer.start()
        self._running = True
        logger.info(
            "Response handler started | topic=%s group=%s",
            settings.kafka_topic_outbound,
            _RESPONSE_GROUP,
        )

    async def stop(self) -> None:
        self._running = False
        if self._consumer:
            await self._consumer.stop()
            logger.info("Response handler stopped.")

    async def run(self) -> None:
        """Main loop — consumes and routes responses until stopped."""
        await self.start()
        try:
            async for kafka_msg in self._consumer:
                if not self._running:
                    break
                await self._handle_with_retry(kafka_msg)
        finally:
            await self.stop()

    # ── Retry wrapper ──────────────────────────────────────────────────────────

    async def _handle_with_retry(self, kafka_msg) -> None:
        """Handle one response with retries. Always commits the offset."""
        payload: dict = kafka_msg.value
        outbound_id = payload.get("outbound_message_id", "unknown")

        for attempt in range(_MAX_RETRIES):
            try:
                await self._route_response(payload)
                break

            except Exception as exc:
                if attempt < _MAX_RETRIES - 1:
                    wait_s = _RETRY_BACKOFF_BASE_S ** attempt
                    logger.warning(
                        "Delivery attempt %d/%d failed for outbound_id=%s: %s. "
                        "Retrying in %ds.",
                        attempt + 1,
                        _MAX_RETRIES,
                        outbound_id,
                        exc,
                        wait_s,
                    )
                    await asyncio.sleep(wait_s)
                else:
                    logger.error(
                        "All delivery attempts exhausted for outbound_id=%s: %s",
                        outbound_id,
                        exc,
                        exc_info=True,
                    )
                    await self._mark_delivery_failed(
                        outbound_id=outbound_id,
                        error=str(exc),
                    )

        try:
            await self._consumer.commit()
        except KafkaError as exc:
            logger.error("Failed to commit offset in response handler: %s", exc)

    # ── Channel router ─────────────────────────────────────────────────────────

    async def _route_response(self, payload: dict) -> None:
        """Dispatch to the appropriate channel delivery method."""
        channel = payload.get("channel", "")
        outbound_id = payload.get("outbound_message_id", "unknown")

        logger.info(
            "Routing response: outbound_id=%s channel=%s", outbound_id, channel
        )

        if channel == "whatsapp":
            await self._deliver_whatsapp(payload)
        elif channel == "gmail":
            await self._deliver_gmail(payload)
        elif channel == "web":
            await self._update_web_status(payload)
        else:
            logger.warning(
                "Unknown channel %r for outbound_id=%s — no delivery action.",
                channel,
                outbound_id,
            )

    # ── WhatsApp delivery ──────────────────────────────────────────────────────

    async def _deliver_whatsapp(self, payload: dict) -> None:
        """
        Verify or retry WhatsApp delivery.

        The send_response tool already attempted delivery; this handler checks
        whether it succeeded (status=replied) and retries if not.
        """
        outbound_id = payload.get("outbound_message_id", "")
        phone = payload.get("customer_phone", "")
        content = payload.get("content", "")

        if not phone:
            logger.warning(
                "WhatsApp delivery skipped — no customer_phone in payload "
                "(outbound_id=%s).",
                outbound_id,
            )
            return

        # Check if the tool already delivered successfully
        if outbound_id:
            async with AsyncSessionFactory() as session:
                msg_repo = MessageRepository(session)
                outbound = await msg_repo.get(uuid.UUID(outbound_id))
                if outbound and outbound.status == MessageStatus.replied:
                    logger.debug(
                        "WhatsApp already delivered by send_response tool: "
                        "outbound_id=%s",
                        outbound_id,
                    )
                    return

        # Tool delivery failed or was skipped — send now
        logger.info(
            "Retrying WhatsApp delivery: outbound_id=%s phone=%s", outbound_id, phone
        )
        url = (
            f"{settings.whatsapp_api_url}"
            f"/{settings.whatsapp_phone_number_id}/messages"
        )
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                url,
                json={
                    "messaging_product": "whatsapp",
                    "to": phone,
                    "type": "text",
                    "text": {"body": content},
                },
                headers={"Authorization": f"Bearer {settings.whatsapp_access_token}"},
            )
            resp.raise_for_status()

        await self._update_delivery_status(outbound_id, "whatsapp_delivered")
        logger.info(
            "WhatsApp delivered: outbound_id=%s phone=%s", outbound_id, phone
        )

    # ── Gmail / email delivery ─────────────────────────────────────────────────

    async def _deliver_gmail(self, payload: dict) -> None:
        """
        Send the agent reply by email.

        Delivery strategy (in priority order):
          1. Gmail API reply (in-thread) if gmail credentials are configured.
          2. SMTP fallback if smtp_host is set in config.
        """
        outbound_id = payload.get("outbound_message_id", "")
        to_email = payload.get("customer_email", "")
        content = payload.get("content", "")
        thread_id = payload.get("gmail_thread_id") or None
        subject = "Re: Your support request"

        if not to_email:
            logger.warning(
                "Email delivery skipped — no customer_email in payload "
                "(outbound_id=%s).",
                outbound_id,
            )
            return

        logger.info(
            "Delivering email reply: outbound_id=%s to=%s thread_id=%s",
            outbound_id,
            to_email,
            thread_id,
        )

        # Strategy 1: Gmail API (preferred — keeps replies in the same thread)
        try:
            await gmail_service.send_reply(
                to_email=to_email,
                subject=subject,
                body=content,
                thread_id=thread_id,
            )
            await self._update_delivery_status(outbound_id, "gmail_api_delivered")
            logger.info(
                "Email sent via Gmail API: outbound_id=%s to=%s", outbound_id, to_email
            )
            return
        except Exception as exc:
            logger.warning(
                "Gmail API delivery failed (outbound_id=%s): %s. "
                "Falling back to SMTP.",
                outbound_id,
                exc,
            )

        # Strategy 2: SMTP fallback
        if not settings.smtp_host:
            raise RuntimeError(
                f"Gmail API failed and smtp_host is not configured — "
                f"cannot deliver email for outbound_id={outbound_id}"
            )

        await self._deliver_via_smtp(
            to_email=to_email,
            subject=subject,
            body=content,
        )
        await self._update_delivery_status(outbound_id, "smtp_delivered")
        logger.info(
            "Email sent via SMTP: outbound_id=%s to=%s", outbound_id, to_email
        )

    async def _deliver_via_smtp(
        self,
        to_email: str,
        subject: str,
        body: str,
    ) -> None:
        """
        Send an email via SMTP using the shared helper.

        Config keys: smtp_host, smtp_port, smtp_user, smtp_password,
                     smtp_from_email, smtp_use_tls.
        """
        from app.services.notification_service import send_smtp_email
        
        await send_smtp_email(to_email=to_email, subject=subject, body=body)
        logger.debug(
            "SMTP delivery complete: to=%s via=%s:%d",
            to_email,
            settings.smtp_host,
            settings.smtp_port,
        )

    # ── Web status update ──────────────────────────────────────────────────────

    async def _update_web_status(self, payload: dict) -> None:
        """
        For the web channel the reply is already in the DB (the send_response
        tool saved it and the Next.js frontend polls for it).

        This handler updates the linked ticket status:
          - Normal reply   → waiting_customer (ball is in the customer's court)
          - Escalated      → escalated        (already set by the agent tool)
        """
        conversation_id_str = payload.get("conversation_id", "")
        was_escalated = payload.get("was_escalated", False)
        outbound_id = payload.get("outbound_message_id", "unknown")

        if not conversation_id_str:
            logger.warning(
                "Web status update skipped — no conversation_id in payload "
                "(outbound_id=%s).",
                outbound_id,
            )
            return

        conversation_id = uuid.UUID(conversation_id_str)

        async with AsyncSessionFactory() as session:
            ticket_repo = TicketRepository(session)
            tickets = await ticket_repo.list_by_conversation(conversation_id)

            updated = 0
            for ticket in tickets:
                # Don't overwrite escalated/resolved/closed statuses
                if ticket.status in (
                    TicketStatus.escalated,
                    TicketStatus.resolved,
                    TicketStatus.closed,
                ):
                    continue

                new_status = (
                    TicketStatus.escalated
                    if was_escalated
                    else TicketStatus.waiting_customer
                )
                await ticket_repo.update(ticket, status=new_status)
                updated += 1

            await session.commit()

        logger.info(
            "Web ticket status updated: conversation_id=%s tickets=%d "
            "escalated=%s outbound_id=%s",
            conversation_id,
            updated,
            was_escalated,
            outbound_id,
        )

    # ── Delivery status helpers ────────────────────────────────────────────────

    async def _update_delivery_status(
        self, outbound_id: str, delivery_status: str
    ) -> None:
        """Stamp the outbound message's processing_metadata with the delivery outcome."""
        if not outbound_id:
            return
        try:
            async with AsyncSessionFactory() as session:
                msg_repo = MessageRepository(session)
                msg = await msg_repo.get(uuid.UUID(outbound_id))
                if msg:
                    await msg_repo.update(
                        msg,
                        processing_metadata={
                            **msg.processing_metadata,
                            "delivery_status": delivery_status,
                            "delivered_at": datetime.now(timezone.utc).isoformat(),
                        },
                    )
                await session.commit()
        except Exception as exc:
            logger.warning(
                "Could not update delivery status for outbound_id=%s: %s",
                outbound_id,
                exc,
            )

    async def _mark_delivery_failed(self, outbound_id: str, error: str) -> None:
        """Record a permanent delivery failure on the outbound message."""
        if not outbound_id:
            return
        try:
            async with AsyncSessionFactory() as session:
                msg_repo = MessageRepository(session)
                msg = await msg_repo.get(uuid.UUID(outbound_id))
                if msg:
                    await msg_repo.update(
                        msg,
                        status=MessageStatus.failed,
                        error_details={"delivery_error": error},
                        processing_metadata={
                            **msg.processing_metadata,
                            "delivery_status": "failed",
                            "delivery_error": error,
                            "failed_at": datetime.now(timezone.utc).isoformat(),
                        },
                    )
                await session.commit()
        except Exception as exc:
            logger.warning(
                "Could not mark delivery failed for outbound_id=%s: %s",
                outbound_id,
                exc,
            )


# ── Standalone entry point ─────────────────────────────────────────────────────


async def main() -> None:
    from app.logging_config import configure_logging
    configure_logging()
    logger.info("Starting Response Handler …")

    handler = ResponseHandler()
    loop = asyncio.get_event_loop()

    def _shutdown() -> None:
        logger.info("Shutdown signal received — stopping response handler.")
        asyncio.create_task(handler.stop())

    loop.add_signal_handler(signal.SIGTERM, _shutdown)
    loop.add_signal_handler(signal.SIGINT, _shutdown)

    try:
        await handler.run()
    finally:
        logger.info("Response handler process exited cleanly.")


if __name__ == "__main__":
    asyncio.run(main())
