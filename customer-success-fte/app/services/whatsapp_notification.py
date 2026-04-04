"""
WhatsApp Notification Service

Sends notifications via Meta Cloud API.
Used for ticket updates, SLA breaches, and alerts.
"""

import logging
from typing import Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class WhatsAppNotificationService:
    """
    Sends WhatsApp messages via the Meta Cloud API.

    Usage:
        service = WhatsAppNotificationService()
        await service.send_message(
            to_phone="+1234567890",
            message="Your ticket #1234 has been updated."
        )
    """

    def __init__(self):
        self.base_url = settings.whatsapp_api_url.rstrip("/")
        self.phone_number_id = settings.whatsapp_phone_number_id
        self.access_token = settings.whatsapp_access_token
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    async def send_message(
        self,
        to_phone: str,
        message: str,
    ) -> dict:
        """
        Send a text message via WhatsApp Cloud API.

        Args:
            to_phone: Recipient phone number in E.164 format (e.g., +1234567890)
            message: Text message to send

        Returns:
            dict: Meta API response with message_id
        """
        if not self.phone_number_id or not self.access_token:
            logger.error("WhatsApp credentials not configured")
            return {"error": "WhatsApp not configured"}

        endpoint = f"/{self.phone_number_id}/messages"

        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "text",
            "text": {"body": message},
        }

        try:
            client = await self._get_client()
            response = await client.post(endpoint, json=payload)
            response.raise_for_status()
            result = response.json()

            logger.info(
                "WhatsApp message sent: to=%s message_id=%s",
                to_phone,
                result.get("messages", [{}])[0].get("id"),
            )
            return result

        except httpx.HTTPStatusError as e:
            logger.error(
                "WhatsApp API error: status=%d response=%s",
                e.response.status_code,
                e.response.text,
            )
            return {"error": f"API error: {e.response.status_code}", "details": e.response.text}

        except Exception as e:
            logger.error("Failed to send WhatsApp message: %s", e, exc_info=True)
            return {"error": str(e)}

    async def send_ticket_notification(
        self,
        to_phone: str,
        ticket_id: str,
        status: str,
        subject: str,
    ) -> dict:
        """
        Send a formatted ticket notification.

        Args:
            to_phone: Recipient phone number
            ticket_id: Ticket ID (e.g., TKT-1234)
            status: Ticket status (open, in_progress, resolved, etc.)
            subject: Ticket subject/description

        Returns:
            dict: Meta API response
        """
        message = (
            f"🎫 *Ticket Update*\n\n"
            f"*Ticket:* {ticket_id}\n"
            f"*Status:* {status.replace('_', ' ').title()}\n"
            f"*Subject:* {subject}\n\n"
            f"Reply to this message or check your dashboard for details."
        )

        return await self.send_message(to_phone, message)

    async def send_sla_breach_alert(
        self,
        to_phone: str,
        ticket_id: str,
        breach_type: str,
    ) -> dict:
        """
        Send an SLA breach alert message.

        Args:
            to_phone: Recipient phone number
            ticket_id: Ticket ID
            breach_type: Type of breach (first_response, resolution)

        Returns:
            dict: Meta API response
        """
        message = (
            f"⚠️ *SLA Breach Alert*\n\n"
            f"*Ticket:* {ticket_id}\n"
            f"*Breach Type:* {breach_type.replace('_', ' ').title()}\n\n"
            f"Immediate action required. Check your dashboard."
        )

        return await self.send_message(to_phone, message)

    async def close(self):
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


# Singleton instance
_whatsapp_service: Optional[WhatsAppNotificationService] = None


def get_whatsapp_service() -> WhatsAppNotificationService:
    """Get or create WhatsApp notification service singleton."""
    global _whatsapp_service
    if _whatsapp_service is None:
        _whatsapp_service = WhatsAppNotificationService()
    return _whatsapp_service
