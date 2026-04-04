"""
Router: WhatsApp notification sending endpoints.

POST /api/notifications/whatsapp — Send a WhatsApp notification
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.services.whatsapp_notification import get_whatsapp_service, WhatsAppNotificationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


class WhatsAppMessageRequest(BaseModel):
    """Request body for sending WhatsApp notification."""
    to_phone: str = Field(..., description="Recipient phone number in E.164 format")
    message: str = Field(..., description="Message text to send")


class TicketNotificationRequest(BaseModel):
    """Request body for sending ticket notification."""
    to_phone: str = Field(..., description="Recipient phone number")
    ticket_id: str = Field(..., description="Ticket ID (e.g., TKT-1234)")
    status: str = Field(..., description="Ticket status")
    subject: str = Field(..., description="Ticket subject/description")


class SLABreachRequest(BaseModel):
    """Request body for sending SLA breach alert."""
    to_phone: str = Field(..., description="Recipient phone number")
    ticket_id: str = Field(..., description="Ticket ID")
    breach_type: str = Field(..., description="Type of breach (first_response, resolution)")


@router.post("/whatsapp", summary="Send WhatsApp text message")
async def send_whatsapp_message(
    request: WhatsAppMessageRequest,
    service: WhatsAppNotificationService = Depends(get_whatsapp_service),
):
    """
    Send a WhatsApp message to any phone number.

    Requires valid WhatsApp Cloud API credentials in .env
    """
    result = await service.send_message(
        to_phone=request.to_phone,
        message=request.message,
    )

    if "error" in result:
        raise HTTPException(status_code=500, detail=result)

    return {"status": "sent", "result": result}


@router.post("/whatsapp/ticket", summary="Send ticket notification via WhatsApp")
async def send_ticket_notification(
    request: TicketNotificationRequest,
    service: WhatsAppNotificationService = Depends(get_whatsapp_service),
):
    """
    Send a formatted ticket notification via WhatsApp.
    """
    result = await service.send_ticket_notification(
        to_phone=request.to_phone,
        ticket_id=request.ticket_id,
        status=request.status,
        subject=request.subject,
    )

    if "error" in result:
        raise HTTPException(status_code=500, detail=result)

    return {"status": "sent", "result": result}


@router.post("/whatsapp/sla-breach", summary="Send SLA breach alert via WhatsApp")
async def send_sla_breach_alert(
    request: SLABreachRequest,
    service: WhatsAppNotificationService = Depends(get_whatsapp_service),
):
    """
    Send an SLA breach alert via WhatsApp.
    """
    result = await service.send_sla_breach_alert(
        to_phone=request.to_phone,
        ticket_id=request.ticket_id,
        breach_type=request.breach_type,
    )

    if "error" in result:
        raise HTTPException(status_code=500, detail=result)

    return {"status": "sent", "result": result}
