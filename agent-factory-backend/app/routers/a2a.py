"""
A2A Protocol Router.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def a2a_root():
    """A2A Protocol root endpoint."""
    return {
        "protocol": "A2A",
        "version": "1.0.0",
        "status": "active",
    }


@router.post("/message")
async def handle_message(message: dict):
    """Handle incoming A2A message."""
    return {
        "status": "received",
        "message_id": message.get("id", "unknown"),
    }
