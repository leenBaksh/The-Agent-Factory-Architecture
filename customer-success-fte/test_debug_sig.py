"""Debug WhatsApp signature verification"""
import hashlib
import hmac
import json
import httpx
import asyncio

SECRET = "my-app-secret-for-testing-12345678"

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
                    "text": {"body": "Hi, I need help with my order"},
                    "type": "text"
                }]
            },
            "field": "messages"
        }]
    }]
}

# httpx will serialize json differently - let's see what it actually sends
body = json.dumps(payload)
expected_sig = "sha256=" + hmac.new(
    SECRET.encode(),
    body.encode(),
    hashlib.sha256
).hexdigest()

print(f"Secret used: {SECRET}")
print(f"Body (first 100 chars): {body[:100]}")
print(f"Signature: {expected_sig}")
print()

async def test():
    async with httpx.AsyncClient() as client:
        # Let's also print what body httpx is actually sending
        # by using data= instead of json= to have full control
        response = await client.post(
            "http://localhost:8000/webhooks/whatsapp",
            content=body.encode(),  # Send exact bytes we signed
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": expected_sig
            }
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

asyncio.run(test())
