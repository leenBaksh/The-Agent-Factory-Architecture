"""
WhatsApp MCP Server for Digital FTEs

Provides tool access for:
- Sending WhatsApp messages (text, templates, media)
- Reading message status and delivery receipts
- Managing WhatsApp Business profile
"""

import os
import logging
from typing import Optional
import httpx

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    "whatsapp-server",
    description="WhatsApp Business API integration for customer notifications",
    dependencies=["httpx"],
)

# Configuration
WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL", "https://graph.facebook.com/v19.0")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")


async def get_headers() -> dict:
    """Get authorization headers for WhatsApp API."""
    if not WHATSAPP_ACCESS_TOKEN:
        raise ValueError("WHATSAPP_ACCESS_TOKEN environment variable not set")
    
    return {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }


@mcp.tool()
async def send_whatsapp_message(
    to_phone: str,
    message: str,
) -> dict:
    """
    Send a WhatsApp text message to a customer.

    Args:
        to_phone: Recipient phone number in E.164 format (e.g., +923001234567)
        message: Text message to send (max 4096 characters)

    Returns:
        dict with message_id and status
    """
    if not WHATSAPP_PHONE_NUMBER_ID:
        return {"success": False, "error": "WHATSAPP_PHONE_NUMBER_ID not configured"}
    
    url = f"{WHATSAPP_API_URL}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_phone,
        "type": "text",
        "text": {
            "body": message[:4096]  # WhatsApp limit
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url,
                json=payload,
                headers=await get_headers(),
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "success": True,
                "message_id": data.get("messages", [{}])[0].get("id"),
                "to": to_phone,
            }
        except httpx.HTTPError as e:
            logger.error(f"WhatsApp message failed: {e}")
            return {"success": False, "error": str(e)}


@mcp.tool()
async def send_whatsapp_template(
    to_phone: str,
    template_name: str,
    language_code: str = "en_US",
    components: Optional[list] = None,
) -> dict:
    """
    Send a WhatsApp template message (for proactive notifications).

    Args:
        to_phone: Recipient phone number in E.164 format
        template_name: Approved template name from Meta
        language_code: Template language (default: en_US)
        components: Optional template components for variables

    Returns:
        dict with message_id and status
    """
    if not WHATSAPP_PHONE_NUMBER_ID:
        return {"success": False, "error": "WHATSAPP_PHONE_NUMBER_ID not configured"}
    
    url = f"{WHATSAPP_API_URL}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language_code},
        }
    }
    
    if components:
        payload["template"]["components"] = components

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url,
                json=payload,
                headers=await get_headers(),
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "success": True,
                "message_id": data.get("messages", [{}])[0].get("id"),
                "template": template_name,
            }
        except httpx.HTTPError as e:
            logger.error(f"WhatsApp template message failed: {e}")
            return {"success": False, "error": str(e)}


@mcp.tool()
async def send_ticket_notification(
    to_phone: str,
    ticket_id: str,
    status: str,
    subject: str,
) -> dict:
    """
    Send a formatted ticket notification via WhatsApp.

    Args:
        to_phone: Recipient phone number in E.164 format
        ticket_id: Ticket ID (e.g., TKT-2026-1500)
        status: Ticket status (open, in_progress, resolved, closed)
        subject: Ticket subject/description

    Returns:
        dict with message_id and status
    """
    emoji_map = {
        "open": "🆕",
        "in_progress": "🔄",
        "resolved": "✅",
        "closed": "🔒",
        "waiting_customer": "⏳",
    }
    
    emoji = emoji_map.get(status, "📋")
    
    message = f"""{emoji} *Ticket Update*

*Ticket ID:* {ticket_id}
*Status:* {status.replace('_', ' ').title()}
*Subject:* {subject}

Reply to this message for support."""

    return await send_whatsapp_message(to_phone, message)


@mcp.tool()
async def send_sla_breach_alert(
    to_phone: str,
    ticket_id: str,
    breach_type: str,
    time_remaining: Optional[str] = None,
) -> dict:
    """
    Send an SLA breach alert via WhatsApp (urgent notification).

    Args:
        to_phone: Recipient phone number (support team member)
        ticket_id: Ticket ID at risk
        breach_type: Type of breach (first_response, resolution)
        time_remaining: Optional time remaining before breach

    Returns:
        dict with message_id and status
    """
    urgency = "⚠️ WARNING" if time_remaining else "🚨 BREACHED"
    
    message = f"""{urgency} *SLA Alert*

*Ticket:* {ticket_id}
*Breach Type:* {breach_type.replace('_', ' ').title()}"""
    
    if time_remaining:
        message += f"\n*Time Remaining:* {time_remaining}"
    else:
        message += "\n*Status:* SLA BREACHED"
    
    message += "\n\nPlease take immediate action."

    return await send_whatsapp_message(to_phone, message)


@mcp.tool()
async def get_message_status(
    message_id: str,
) -> dict:
    """
    Get delivery status of a WhatsApp message.

    Args:
        message_id: WhatsApp message ID from send response

    Returns:
        dict with delivery status (sent, delivered, read, failed)
    """
    if not WHATSAPP_PHONE_NUMBER_ID:
        return {"success": False, "error": "WHATSAPP_PHONE_NUMBER_ID not configured"}
    
    url = f"{WHATSAPP_API_URL}/{message_id}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url,
                headers=await get_headers(),
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "success": True,
                "message_id": message_id,
                "status": data.get("status"),
                "timestamp": data.get("timestamp"),
            }
        except httpx.HTTPError as e:
            logger.error(f"WhatsApp status check failed: {e}")
            return {"success": False, "error": str(e)}


if __name__ == "__main__":
    mcp.run()
