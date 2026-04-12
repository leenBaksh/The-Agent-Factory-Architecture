"""Quick WhatsApp webhook test with correct signature"""
import hashlib
import hmac
import json
import asyncio
import httpx

APP_SECRET = "my-app-secret-for-testing-12345678"  # From your .env file

payload = {
    "object": "whatsapp_business_account",
    "entry": [{
        "id": "123",
        "changes": [{
            "value": {
                "messaging_product": "whatsapp",
                "metadata": {
                    "display_phone_number": "15551234567",
                    "phone_number_id": "123456789"
                },
                "contacts": [{
                    "profile": {"name": "Test Customer"},
                    "wa_id": "923001234567"
                }],
                "messages": [{
                    "from": "923001234567",
                    "id": "wamid.test123",
                    "timestamp": "1234567890",
                    "text": {
                        "body": "Hi, I need help with my order #12345. It has not arrived yet."
                    },
                    "type": "text"
                }]
            },
            "field": "messages"
        }]
    }]
}

body = json.dumps(payload)
signature = "sha256=" + hmac.new(
    APP_SECRET.encode(),
    body.encode(),
    hashlib.sha256
).hexdigest()

async def test():
    print("\n📱 Sending test WhatsApp message to webhook...")
    print(f"   From: +923001234567")
    print(f"   Message: Hi, I need help with my order #12345")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/webhooks/whatsapp",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": signature
            }
        )
        print(f"\n✅ Status: {response.status_code}")
        print(f"   Response: {response.text}")

asyncio.run(test())
