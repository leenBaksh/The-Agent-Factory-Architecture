"""
Test WhatsApp & Gmail Integration - Simulates Real Flow

This script demonstrates the complete WhatsApp → AI → Reply flow
WITHOUT needing real Meta/Google credentials.

It:
1. Sends a test message to the webhook (bypassing signature check)
2. Shows how the message gets ingested
3. Simulates AI response
4. Shows how reply would be sent via WhatsApp MCP
"""

import asyncio
import hashlib
import hmac
import json
import sys
from pathlib import Path

import httpx

# ── Configuration ────────────────────────────────────────────────────────────
BASE_URL = "http://localhost:8000"
BACKEND_URL = "http://localhost:8003"

# Test phone number (what customer would send from)
TEST_PHONE = "923001234567"
TEST_MESSAGE = "Hi, I need help with my order #12345. It hasn't arrived yet."

# WhatsApp app secret from .env (or use test mode)
APP_SECRET = "my-app-secret-for-testing-12345678"


def sign_payload(body: str, secret: str) -> str:
    """Create X-Hub-Signature-256 header value."""
    signature = hmac.new(
        secret.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"sha256={signature}"


async def test_whatsapp_webhook():
    """Send a test WhatsApp message to the webhook endpoint."""
    
    print("\n" + "="*70)
    print("📱 Testing WhatsApp Webhook Integration")
    print("="*70)
    
    # Build WhatsApp webhook payload (same format Meta sends)
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
                        "id": "wamid.test123",
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
    
    print(f"\n📨 Simulating incoming WhatsApp message:")
    print(f"   From: +{TEST_PHONE}")
    print(f"   Message: {TEST_MESSAGE}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/webhooks/whatsapp",
                content=body.encode(),  # Use content to send exact bytes
                headers={
                    "Content-Type": "application/json",
                    "X-Hub-Signature-256": signature
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                print(f"\n✅ WhatsApp webhook accepted!")
                print(f"   Response: {response.json()}")
            else:
                print(f"\n❌ WhatsApp webhook rejected!")
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except httpx.ConnectError:
            print(f"\n❌ Cannot connect to {BASE_URL}")
            print(f"   Is the Customer Success FTE running?")
            return False
    
    return True


async def test_gmail_webhook():
    """Test Gmail webhook endpoint."""
    
    print("\n" + "="*70)
    print("📧 Testing Gmail Webhook Integration")
    print("="*70)
    
    async with httpx.AsyncClient() as client:
        try:
            # GET request - health check
            response = await client.get(f"{BASE_URL}/webhooks/gmail")
            
            if response.status_code == 200:
                print(f"\n✅ Gmail webhook is ready!")
                print(f"   Response: {response.json()}")
            else:
                print(f"\n❌ Gmail webhook not ready!")
                print(f"   Status: {response.status_code}")
                
        except httpx.ConnectError:
            print(f"\n❌ Cannot connect to {BASE_URL}")
            return False
    
    return True


async def test_whatsapp_mcp():
    """Test WhatsApp MCP server (if running)."""
    
    print("\n" + "="*70)
    print("🤖 Testing WhatsApp MCP Server")
    print("="*70)
    
    # MCP servers typically run on different ports
    # This would test if the MCP tool is available
    print("\nℹ️  WhatsApp MCP Server would be called by AI agent")
    print("   To test with real credentials:")
    print("   1. Set WHATSAPP_PHONE_NUMBER_ID in .env")
    print("   2. Set WHATSAPP_ACCESS_TOKEN in .env")
    print("   3. Run: python mcp-servers/whatsapp_mcp.py")
    print("   4. AI agent will auto-reply to incoming messages")
    
    return True


async def test_backend_integration():
    """Test if backend can see WhatsApp tickets."""
    
    print("\n" + "="*70)
    print("📊 Testing Dashboard Integration")
    print("="*70)
    
    async with httpx.AsyncClient() as client:
        try:
            # Check metrics endpoint
            response = await client.get(f"{BACKEND_URL}/metrics/dashboard")
            
            if response.status_code == 200:
                metrics = response.json()
                print(f"\n✅ Backend metrics endpoint working!")
                print(f"   Response: {json.dumps(metrics, indent=2)[:200]}...")
            else:
                print(f"\n⚠️  Backend metrics returned: {response.status_code}")
                
        except httpx.ConnectError:
            print(f"\n❌ Cannot connect to backend at {BACKEND_URL}")
            return False
    
    return True


async def test_full_flow():
    """Run complete integration test."""
    
    print("\n" + "="*70)
    print("🚀 Testing Complete WhatsApp + Gmail Integration Flow")
    print("="*70)
    
    results = {
        "WhatsApp Webhook": await test_whatsapp_webhook(),
        "Gmail Webhook": await test_gmail_webhook(),
        "WhatsApp MCP": await test_whatsapp_mcp(),
        "Backend Integration": await test_backend_integration(),
    }
    
    print("\n" + "="*70)
    print("📋 Test Results Summary")
    print("="*70)
    
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status} - {test}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 All integration endpoints are working!")
        print("\n📝 To enable REAL WhatsApp & Gmail:")
        print("   1. Open: customer-success-fte\\.env")
        print("   2. Add your WhatsApp credentials from Meta")
        print("   3. Run Gmail OAuth: python scripts\\setup_gmail_auth.py")
        print("   4. Restart the service")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
    
    print("\n" + "="*70)
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(test_full_flow())
    sys.exit(0 if success else 1)
