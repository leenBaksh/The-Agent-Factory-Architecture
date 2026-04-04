#!/usr/bin/env python3
"""
Test WhatsApp Notification Service

Sends a test message to verify WhatsApp integration is working.

Usage:
    python test_whatsapp.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.whatsapp_notification import WhatsAppNotificationService


async def main():
    """Send test WhatsApp message."""
    print("📱 Testing WhatsApp Notification Service...")
    
    service = WhatsAppNotificationService()
    
    # Test 1: Simple message
    print("\n1️⃣  Sending test message...")
    result = await service.send_message(
        to_phone="+923001234567",  # Replace with your number
        message="🎉 *Agent Factory Test*\n\nWhatsApp integration is working!\n\nThis is a test message from your Digital FTE system.",
    )
    
    if "error" in result:
        print(f"❌ Failed: {result}")
    else:
        print(f"✅ Success! Message ID: {result.get('messages', [{}])[0].get('id')}")
    
    # Test 2: Ticket notification
    print("\n2️⃣  Sending ticket notification...")
    result = await service.send_ticket_notification(
        to_phone="+923001234567",  # Replace with your number
        ticket_id="TKT-001",
        status="open",
        subject="Test ticket for WhatsApp integration",
    )
    
    if "error" in result:
        print(f"❌ Failed: {result}")
    else:
        print(f"✅ Success! Message ID: {result.get('messages', [{}])[0].get('id')}")
    
    await service.close()
    print("\n✅ Test complete!")


if __name__ == "__main__":
    asyncio.run(main())
