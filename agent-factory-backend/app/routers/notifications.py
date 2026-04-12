"""
Notifications Router - Manages notifications for the dashboard.
"""

import logging
import random
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory notification store (replace with database in production)
notifications_store: list[dict[str, Any]] = []


class WhatsAppMessageRequest(BaseModel):
    to_phone: str = ""
    message: str = ""


def _generate_mock_notifications() -> list[dict[str, Any]]:
    """Generate realistic mock notifications."""
    now = datetime.now()

    return [
        {
            "id": "1",
            "type": "info",
            "title": "New Ticket Assigned",
            "message": "Ticket #1234 has been assigned to your queue. Priority: High. Customer: Acme Corp.",
            "timestamp": (now - timedelta(minutes=2)).isoformat(),
            "read": False,
        },
        {
            "id": "2",
            "type": "warning",
            "title": "SLA Breach Warning",
            "message": "Ticket #1230 is approaching SLA breach threshold (15 min remaining). Response time SLA: 95%.",
            "timestamp": (now - timedelta(minutes=15)).isoformat(),
            "read": False,
        },
        {
            "id": "3",
            "type": "success",
            "title": "Ticket Resolved",
            "message": "Ticket #1225 has been resolved successfully by Customer Success FTE. Resolution time: 45 minutes.",
            "timestamp": (now - timedelta(hours=1)).isoformat(),
            "read": False,
        },
        {
            "id": "4",
            "type": "error",
            "title": "FTE Health Check Failed",
            "message": "Technical Support FTE failed health check. Automatic restart initiated. Expected downtime: 2 minutes.",
            "timestamp": (now - timedelta(hours=2)).isoformat(),
            "read": True,
        },
        {
            "id": "5",
            "type": "success",
            "title": "New FTE Deployed",
            "message": "Sales Support FTE v1.2.0 deployed successfully. All skills updated and A2A protocol active.",
            "timestamp": (now - timedelta(days=1)).isoformat(),
            "read": True,
        },
    ]


@router.get("/notifications", tags=["Notifications"])
async def get_notifications() -> dict[str, Any]:
    """Get all notifications."""
    global notifications_store

    # Initialize with mock data if empty
    if not notifications_store:
        notifications_store = _generate_mock_notifications()

    unread_count = sum(1 for n in notifications_store if not n["read"])

    return {
        "notifications": notifications_store,
        "unread_count": unread_count,
        "total_count": len(notifications_store),
    }


@router.post("/notifications/{notification_id}/read", tags=["Notifications"])
async def mark_as_read(notification_id: str) -> dict[str, Any]:
    """Mark a notification as read."""
    global notifications_store

    for notif in notifications_store:
        if notif["id"] == notification_id:
            notif["read"] = True
            return {"success": True, "message": "Notification marked as read"}

    return {"success": False, "message": "Notification not found"}


@router.post("/notifications/mark-all-read", tags=["Notifications"])
async def mark_all_as_read() -> dict[str, Any]:
    """Mark all notifications as read."""
    global notifications_store

    for notif in notifications_store:
        notif["read"] = True

    return {"success": True, "message": "All notifications marked as read"}


@router.delete("/notifications/{notification_id}", tags=["Notifications"])
async def delete_notification(notification_id: str) -> dict[str, Any]:
    """Delete a notification."""
    global notifications_store

    initial_len = len(notifications_store)
    notifications_store = [n for n in notifications_store if n["id"] != notification_id]

    if len(notifications_store) < initial_len:
        return {"success": True, "message": "Notification deleted"}

    return {"success": False, "message": "Notification not found"}


@router.post("/notifications/clear-read", tags=["Notifications"])
async def clear_read_notifications() -> dict[str, Any]:
    """Clear all read notifications."""
    global notifications_store

    initial_count = len(notifications_store)
    notifications_store = [n for n in notifications_store if not n["read"]]
    cleared_count = initial_count - len(notifications_store)

    return {
        "success": True,
        "message": f"Cleared {cleared_count} read notifications",
        "cleared_count": cleared_count,
    }


@router.post("/notifications/whatsapp", tags=["Notifications"])
async def send_whatsapp_notification(msg: WhatsAppMessageRequest) -> dict[str, Any]:
    """Send WhatsApp notification (mock - integrate Twilio/WhatsApp Business API in production)."""
    logger.info(f"WhatsApp notification to {msg.to_phone}: {msg.message[:50]}...")

    return {
        "success": True,
        "message": "WhatsApp notification queued",
        "to": msg.to_phone,
    }
