"""
Router: WhatsApp Cloud API channel (Meta webhooks).

GET  /webhooks/whatsapp — Webhook verification challenge (Meta requires this on setup)
POST /webhooks/whatsapp — Receives inbound message and status events

Security:
  - GET: hub.verify_token compared against settings.whatsapp_verify_token
  - POST: X-Hub-Signature-256 HMAC-SHA256 verified against settings.whatsapp_app_secret
"""

import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import ChannelType, get_db
from app.dependencies.rate_limiting import whatsapp_rate_limit
from app.models.whatsapp import WhatsAppWebhookPayload
from app.services.message_service import MessageService

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


# ── Signature verification ────────────────────────────────────────────────────


def _verify_meta_signature(raw_body: bytes, signature_header: str | None) -> None:
    """
    Verify the X-Hub-Signature-256 header sent by Meta.

    Meta computes: HMAC-SHA256(app_secret, raw_body) and sends it as
    'sha256=<hex_digest>'. We must verify before processing any payload.

    Raises HTTP 403 if verification fails or the header is absent.
    """
    if not settings.whatsapp_app_secret:
        # App secret is required — do not allow bypass in any environment
        logger.error(
            "whatsapp_app_secret not configured. Signature verification cannot proceed."
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server misconfiguration: whatsapp_app_secret not set.",
        )

    if not signature_header:
        logger.warning("WhatsApp POST missing X-Hub-Signature-256 header.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-Hub-Signature-256 header.",
        )

    expected_sig = (
        "sha256="
        + hmac.new(
            settings.whatsapp_app_secret.encode("utf-8"),
            raw_body,
            hashlib.sha256,
        ).hexdigest()
    )

    if not hmac.compare_digest(signature_header, expected_sig):
        logger.warning(
            "WhatsApp signature mismatch — possible spoofed request. "
            "Received: %s",
            signature_header,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Signature verification failed.",
        )


# ── Routes ────────────────────────────────────────────────────────────────────


@router.get(
    "/whatsapp",
    status_code=200,
    summary="WhatsApp webhook verification challenge",
    include_in_schema=False,
)
async def whatsapp_verify(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_verify_token: str = Query(..., alias="hub.verify_token"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
) -> Response:
    """
    Meta webhook verification.

    When you register the webhook URL in the Meta Developer Portal, Meta sends
    a GET with hub.mode=subscribe. We validate the token and echo hub.challenge.
    """
    if hub_mode != "subscribe":
        logger.warning("WhatsApp verify: unexpected hub.mode=%r", hub_mode)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unexpected hub.mode: {hub_mode!r}",
        )

    if not hmac.compare_digest(hub_verify_token, settings.whatsapp_verify_token):
        logger.warning("WhatsApp verify: token mismatch.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Verify token mismatch.",
        )

    logger.info("WhatsApp webhook verified successfully.")
    return Response(content=hub_challenge, media_type="text/plain")


@router.post(
    "/whatsapp",
    status_code=200,
    summary="Receive WhatsApp Cloud API events",
    dependencies=[Depends(whatsapp_rate_limit)],
    responses={
        200: {"description": "Event acknowledged"},
        400: {"description": "Missing signature header"},
        403: {"description": "Signature verification failed"},
        500: {"description": "Internal server error"},
    },
)
async def receive_whatsapp_event(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> dict:
    """
    Processes inbound WhatsApp events from the Meta Cloud API.

    Meta delivers all event types (messages, delivery receipts, read receipts)
    to this single endpoint. We:
      1. Verify X-Hub-Signature-256 against the raw body.
      2. Parse and validate the payload.
      3. Filter for text message events (skip statuses / read receipts).
      4. Resolve customer and ingest via MessageService.

    Returns {"status": "ok"} — Meta requires a 200 within 20 seconds or retries.
    """
    # ── 1. Read raw body before Pydantic consumes it (needed for HMAC) ────────
    raw_body = await request.body()

    # ── 2. Verify Meta signature ──────────────────────────────────────────────
    signature = request.headers.get("X-Hub-Signature-256")
    _verify_meta_signature(raw_body, signature)

    # ── 3. Parse payload ──────────────────────────────────────────────────────
    try:
        payload = WhatsAppWebhookPayload.model_validate(json.loads(raw_body))
    except Exception as exc:
        logger.warning("Failed to parse WhatsApp payload: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid WhatsApp webhook payload.",
        ) from exc

    if payload.object != "whatsapp_business_account":
        logger.debug(
            "Ignoring non-WABA WhatsApp event: object=%r", payload.object
        )
        return {"status": "ok"}

    # ── 4. Process each message event ─────────────────────────────────────────
    svc = MessageService(session)
    ingested = 0
    skipped = 0

    for entry in payload.entry:
        for change in entry.changes:
            if change.field != "messages":
                logger.debug("Skipping WhatsApp change field=%r", change.field)
                continue

            # Delivery/read status updates — no action needed here
            if change.value.statuses:
                logger.debug(
                    "Received %d status update(s) — no action.",
                    len(change.value.statuses),
                )

            for msg in change.value.messages:
                phone_number_id = change.value.metadata.phone_number_id

                if msg.type != "text" or msg.text is None:
                    logger.info(
                        "Skipping unsupported WhatsApp message type=%r "
                        "from=%s id=%s",
                        msg.type,
                        msg.sender,
                        msg.id,
                    )
                    skipped += 1
                    continue

                logger.info(
                    "Processing WhatsApp text message: from=%s id=%s body=%r",
                    msg.sender,
                    msg.id,
                    msg.text.body[:80],
                )

                try:
                    message_id = await svc.ingest(
                        channel=ChannelType.whatsapp,
                        external_id=msg.sender,          # sender phone (E.164)
                        display_name=msg.sender,         # enriched later by agent
                        content=msg.text.body,
                        phone=msg.sender,
                        raw_payload={
                            "whatsapp_message_id": msg.id,
                            "timestamp": msg.timestamp,
                            "phone_number_id": phone_number_id,
                            "waba_entry_id": entry.id,
                            "full_payload": payload.model_dump(mode="json"),
                        },
                    )
                    logger.info(
                        "WhatsApp message ingested: from=%s whatsapp_id=%s "
                        "message_id=%s",
                        msg.sender,
                        msg.id,
                        message_id,
                    )
                    ingested += 1

                except SQLAlchemyError as exc:
                    logger.error(
                        "DB error ingesting WhatsApp message id=%s from=%s: %s",
                        msg.id,
                        msg.sender,
                        exc,
                        exc_info=True,
                    )
                except Exception as exc:
                    logger.error(
                        "Unexpected error ingesting WhatsApp message id=%s: %s",
                        msg.id,
                        exc,
                        exc_info=True,
                    )

    logger.info(
        "WhatsApp batch complete: ingested=%d skipped=%d",
        ingested,
        skipped,
    )
    return {"status": "ok"}
