"""
Router: Web Support Form channel.

POST /api/web/support — receives submissions from the Next.js support form.
Protected by API key auth and per-IP rate limiting.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import ChannelType, get_db
from app.dependencies.auth import require_api_key
from app.dependencies.rate_limiting import web_rate_limit
from app.models.web_form import WebFormResponse, WebFormSubmission
from app.services.message_service import MessageService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/web/support",
    response_model=WebFormResponse,
    status_code=202,
    summary="Receive web support form submission",
    dependencies=[Depends(require_api_key), Depends(web_rate_limit)],
    responses={
        202: {"description": "Accepted — message queued for processing"},
        400: {"description": "Invalid request payload"},
        401: {"description": "Missing API key"},
        403: {"description": "Invalid API key"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"},
    },
)
async def receive_web_form(
    payload: WebFormSubmission,
    session: AsyncSession = Depends(get_db),
) -> WebFormResponse:
    """
    Intake handler for the Next.js web support form.

    Pipeline:
      1. Validate input (Pydantic — 422 returned automatically on failure)
      2. Resolve or create customer by email address
      3. Open or reuse the customer's active web conversation
      4. Persist the inbound message with status=received
      5. Publish to Kafka topic `cs-fte.messages.inbound`
      6. Return 202 Accepted with the tracking ticket_id

    The agent worker picks up the Kafka event asynchronously and sends a reply.
    """
    logger.info(
        "Web form submission received: name=%r email=%s subject=%r",
        payload.name,
        payload.email,
        payload.subject,
    )

    try:
        svc = MessageService(session)
        message_id = await svc.ingest(
            channel=ChannelType.web,
            external_id=payload.email,       # web channel identity = email
            display_name=payload.name,
            content=payload.message,
            subject=payload.subject,
            email=payload.email,
            phone=payload.phone,
            company=payload.company,
            raw_payload=payload.model_dump(mode="json"),
        )
    except SQLAlchemyError as exc:
        logger.exception(
            "Database error while ingesting web form from %s: %s",
            payload.email,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save your submission. Please try again.",
        ) from exc
    except Exception as exc:
        logger.exception(
            "Unexpected error while ingesting web form from %s: %s",
            payload.email,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        ) from exc

    logger.info(
        "Web form ingested successfully: email=%s message_id=%s",
        payload.email,
        message_id,
    )
    return WebFormResponse(ticket_id=message_id)
