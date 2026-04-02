"""
Router: Gmail channel (Cloud Pub/Sub push webhook).

GET  /webhooks/gmail — Health probe (used for manual verification)
POST /webhooks/gmail — Receives push notifications from Google Cloud Pub/Sub

Flow:
  1. Google Pub/Sub POSTs a notification when new mail arrives.
  2. We decode the base64 data payload to extract emailAddress and historyId.
  3. GmailService calls History.list() then Messages.get() to fetch full content.
  4. Each parsed email is saved via MessageService and published to Kafka.
  5. We return 204 to acknowledge the Pub/Sub delivery (non-2xx causes retries).
"""

import base64
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import ChannelType, get_db
from app.dependencies.rate_limiting import gmail_rate_limit
from app.models.gmail import GmailPushNotification
from app.services.gmail_service import gmail_service
from app.services.message_service import MessageService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/gmail",
    status_code=200,
    summary="Gmail webhook health probe",
    include_in_schema=False,
)
async def gmail_health() -> dict:
    """Simple liveness probe — confirms the endpoint is reachable."""
    return {"status": "ok", "channel": "gmail"}


@router.post(
    "/gmail",
    status_code=204,
    summary="Receive Gmail Pub/Sub push notification",
    dependencies=[Depends(gmail_rate_limit)],
    responses={
        204: {"description": "Acknowledged — message queued"},
        400: {"description": "Malformed Pub/Sub payload"},
        500: {"description": "Internal server error"},
    },
)
async def receive_gmail_push(
    notification: GmailPushNotification,
    session: AsyncSession = Depends(get_db),
) -> None:
    """
    Handles a Cloud Pub/Sub push delivery for Gmail.

    Steps:
      1. Base64-decode the Pub/Sub message data to get emailAddress + historyId.
      2. Call GmailService.get_new_messages(historyId) via thread-pool executor.
      3. For each parsed email: resolve customer and call MessageService.ingest().
      4. Return 204 No Content (Pub/Sub requires 2xx within 10s or it retries).

    IMPORTANT: If Gmail API or DB errors occur we still return 204 to avoid
    infinite Pub/Sub retries. Errors are logged for alerting/observability.
    """
    # ── 1. Decode Pub/Sub payload ──────────────────────────────────────────────
    try:
        # Gmail Pub/Sub data is base64-encoded JSON: {"emailAddress": ..., "historyId": ...}
        decoded_bytes = base64.b64decode(notification.message.data + "==")
        data = json.loads(decoded_bytes.decode("utf-8"))
    except Exception as exc:
        logger.warning(
            "Failed to decode Gmail Pub/Sub data (msgId=%s): %s",
            notification.message.message_id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Pub/Sub message data encoding.",
        ) from exc

    history_id: str = str(data.get("historyId", "")).strip()
    email_address: str = data.get("emailAddress", "").strip()

    logger.info(
        "Gmail push received: account=%s historyId=%s pubsubMsgId=%s",
        email_address,
        history_id,
        notification.message.message_id,
    )

    if not history_id:
        logger.warning(
            "Gmail push notification missing historyId — skipping (pubsubMsgId=%s).",
            notification.message.message_id,
        )
        # Return 204 anyway — retrying an empty notification won't help
        return

    # ── 2. Fetch new emails from Gmail API ────────────────────────────────────
    try:
        emails = await gmail_service.get_new_messages(history_id)
    except Exception as exc:
        # Log and re-raise as HTTP 503 — Pub/Sub will retry transient Gmail API errors
        logger.error(
            "Gmail API error for historyId=%s account=%s: %s",
            history_id,
            email_address,
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gmail API temporarily unavailable. Pub/Sub will retry.",
        ) from exc

    if not emails:
        logger.info(
            "No new INBOX messages found for historyId=%s account=%s.",
            history_id,
            email_address,
        )
        return

    logger.info(
        "Processing %d email(s) from Gmail historyId=%s account=%s.",
        len(emails),
        history_id,
        email_address,
    )

    # ── 3. Ingest each email ──────────────────────────────────────────────────
    svc = MessageService(session)
    ingested = 0
    errors = 0

    for parsed in emails:
        logger.debug(
            "Ingesting Gmail message: gmail_id=%s from=%s subject=%r",
            parsed.gmail_id,
            parsed.sender_email,
            parsed.subject,
        )
        try:
            message_id = await svc.ingest(
                channel=ChannelType.gmail,
                external_id=parsed.sender_email,       # Gmail identity = sender address
                display_name=parsed.sender_name or parsed.sender_email,
                content=parsed.body,
                subject=parsed.subject,
                email=parsed.sender_email,
                raw_payload={
                    "gmail_id": parsed.gmail_id,
                    "thread_id": parsed.thread_id,
                    "headers": parsed.raw_headers,
                    "history_id": history_id,
                    "pubsub_message_id": notification.message.message_id,
                },
            )
            logger.info(
                "Gmail message ingested: gmail_id=%s from=%s message_id=%s",
                parsed.gmail_id,
                parsed.sender_email,
                message_id,
            )
            ingested += 1
        except SQLAlchemyError as exc:
            logger.error(
                "DB error ingesting Gmail message gmail_id=%s: %s",
                parsed.gmail_id,
                exc,
                exc_info=True,
            )
            errors += 1
        except Exception as exc:
            logger.error(
                "Unexpected error ingesting Gmail message gmail_id=%s: %s",
                parsed.gmail_id,
                exc,
                exc_info=True,
            )
            errors += 1

    logger.info(
        "Gmail batch complete: ingested=%d errors=%d historyId=%s",
        ingested,
        errors,
        history_id,
    )
    
    # If all emails failed to ingest, return 503 to trigger Pub/Sub retry
    # If some succeeded, return 204 — partial failures are handled via logs/alerts
    if errors > 0 and ingested == 0:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"All {errors} email(s) failed to ingest. Pub/Sub will retry.",
        )
    
    # Return 204 on success or partial success
