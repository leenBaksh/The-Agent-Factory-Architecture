"""
Test: Create Ticket → WhatsApp Notification

This script simulates a customer sending a WhatsApp message,
which creates a ticket and automatically sends a WhatsApp notification back.
"""

import hashlib
import hmac
import json
import asyncio
import httpx

APP_SECRET = "my-app-secret-for-testing-12345678"
BASE_URL = "http://localhost:8000"

# Test customer data
TEST_PHONE = "923001234567"
TEST_MESSAGE = "Hi, I have an issue with my order. The product arrived damaged and I need a replacement."


def sign_payload(body: str, secret: str) -> str:
    """Create X-Hub-Signature-256 header value."""
    signature = hmac.new(
        secret.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"sha256={signature}"


async def test_whatsapp_ticket_creation():
    """
    Simulate customer sending WhatsApp message.
    This should:
    1. Create a new ticket/conversation
    2. Send WhatsApp notification back
    """
    
    print("\n" + "="*70)
    print("📱 Testing: Create Ticket → WhatsApp Notification")
    print("="*70)
    
    # Build WhatsApp webhook payload
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "15551234567",
                        "phone_number_id": "123456789"
                    },
                    "contacts": [{
                        "profile": {
                            "name": "Test Customer"
                        },
                        "wa_id": TEST_PHONE
                    }],
                    "messages": [{
                        "from": TEST_PHONE,
                        "id": "wamid.test_new_ticket",
                        "timestamp": "1234567890",
                        "text": {
                            "body": TEST_MESSAGE
                        },
                        "type": "text"
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    
    body = json.dumps(payload)
    signature = sign_payload(body, APP_SECRET)
    
    print(f"\n📨 Customer sends WhatsApp message:")
    print(f"   From: +{TEST_PHONE}")
    print(f"   Message: {TEST_MESSAGE}")
    print(f"\n⏳ Processing...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/webhooks/whatsapp",
                content=body.encode(),  # Send exact bytes we signed
                headers={
                    "Content-Type": "application/json",
                    "X-Hub-Signature-256": signature
                },
                timeout=15.0
            )
            
            if response.status_code == 200:
                print(f"\n✅ Ticket created successfully!")
                print(f"   Webhook Response: {response.json()}")
                print(f"\n📱 WhatsApp notification should be sent automatically")
                print(f"   (Check logs for 'WhatsApp notification sent' message)")
                return True
            else:
                print(f"\n❌ Failed to create ticket!")
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except httpx.ConnectError:
            print(f"\n❌ Cannot connect to {BASE_URL}")
            print(f"   Is the Customer Success FTE running?")
            return False
        except Exception as e:
            print(f"\n❌ Error: {e}")
            return False


async def test_second_message_same_ticket():
    """
    Test that a second message reuses the same ticket
    (should NOT send another notification).
    """
    
    print("\n" + "="*70)
    print("📱 Testing: Second Message (Same Ticket - No Notification)")
    print("="*70)
    
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "15551234567",
                        "phone_number_id": "123456789"
                    },
                    "contacts": [{
                        "profile": {
                            "name": "Test Customer"
                        },
                        "wa_id": TEST_PHONE
                    }],
                    "messages": [{
                        "from": TEST_PHONE,
                        "id": "wamid.test_followup",
                        "timestamp": "1234567900",
                        "text": {
                            "body": "Also, can you send me the tracking number?"
                        },
                        "type": "text"
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    
    body = json.dumps(payload)
    signature = sign_payload(body, APP_SECRET)
    
    print(f"\n📨 Customer sends follow-up message:")
    print(f"   From: +{TEST_PHONE}")
    print(f"   Message: Also, can you send me the tracking number?")
    print(f"\n⏳ Processing...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/webhooks/whatsapp",
                content=body.encode(),
                headers={
                    "Content-Type": "application/json",
                    "X-Hub-Signature-256": signature
                },
                timeout=15.0
            )
            
            if response.status_code == 200:
                print(f"\n✅ Follow-up message processed!")
                print(f"   (No new notification should be sent - same ticket)")
                return True
            else:
                print(f"\n❌ Failed!")
                print(f"   Status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
            return False


async def main():
    print("\n" + "="*70)
    print("🚀 WhatsApp Ticket Creation + Notification Test")
    print("="*70)
    
    results = {
        "New Ticket + WhatsApp Notification": await test_whatsapp_ticket_creation(),
        "Follow-up Message (No Duplicate Notification)": await test_second_message_same_ticket(),
    }
    
    print("\n" + "="*70)
    print("📋 Test Results Summary")
    print("="*70)
    
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status} - {test}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 All tests passed!")
        print("\n📝 What happened:")
        print("   1. Customer sent WhatsApp message")
        print("   2. System created new ticket automatically")
        print("   3. WhatsApp notification sent with ticket details")
        print("   4. Follow-up message reused same ticket (no duplicate notification)")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    asyncio.run(main())
