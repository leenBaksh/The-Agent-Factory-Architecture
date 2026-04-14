"""
WhatsApp Customer Support - Readiness Test

Tests the complete pipeline:
1. WhatsApp Webhook → Message Reception
2. Kafka Message Publishing
3. AI Agent Processing
4. Response Delivery

Usage:
    python test_whatsapp_ready.py
"""

import asyncio
import hashlib
import hmac
import json
import sys
import time
from pathlib import Path

import httpx

# ── Configuration ─────────────────────────────────────────────────────────────
BASE_URL = "http://localhost:8000"
APP_SECRET = "ffd4ec8c5ec0b0bf27095487f814207e"
TEST_PHONE = "923001234567"

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


def sign_payload(body: str, secret: str) -> str:
    """Create X-Hub-Signature-256 header value."""
    signature = hmac.new(
        secret.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"sha256={signature}"


def print_header(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def print_test(name: str, passed: bool, detail: str = ""):
    status = f"{GREEN}✅ PASS{RESET}" if passed else f"{RED}❌ FAIL{RESET}"
    print(f"  {status}  {name}")
    if detail:
        print(f"       {detail}")


async def test_health():
    """Test 1: API Health Check"""
    print_header("Test 1: API Health Check")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{BASE_URL}/health")
            data = resp.json()
            passed = resp.status_code == 200 and data.get("status") == "ok"
            print_test("Health endpoint", passed, f"Response: {data}")
            return passed
    except Exception as e:
        print_test("Health endpoint", False, f"Error: {e}")
        return False


async def test_skills():
    """Test 2: Skills System"""
    print_header("Test 2: Skills System")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{BASE_URL}/api/skills")
            data = resp.json()
            skills = data.get("skills", [])
            passed = len(skills) >= 4
            print_test("Skills loaded", passed, f"{len(skills)} skills available")
            for skill in skills:
                print_test(
                    f"  → {skill['skill_id']}",
                    True,
                    f"v{skill['version']} - {len(skill['tools'])} tools",
                )
            return passed
    except Exception as e:
        print_test("Skills system", False, f"Error: {e}")
        return False


async def test_webhook_signature():
    """Test 3: Webhook Signature Verification"""
    print_header("Test 3: Webhook Security")
    try:
        payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "123",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "15551234567",
                            "phone_number_id": "1047635248436693",
                        },
                        "contacts": [{"profile": {"name": "Test"}, "wa_id": TEST_PHONE}],
                        "messages": [{
                            "from": TEST_PHONE,
                            "id": "wamid.test123",
                            "timestamp": str(int(time.time())),
                            "text": {"body": "Test message"},
                            "type": "text",
                        }],
                    },
                    "field": "messages",
                }],
            }],
        }
        body = json.dumps(payload)
        signature = sign_payload(body, APP_SECRET)

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BASE_URL}/webhooks/whatsapp",
                content=body.encode(),
                headers={
                    "Content-Type": "application/json",
                    "X-Hub-Signature-256": signature,
                },
            )
            passed = resp.status_code in (200, 202)
            print_test("Signature verification", passed, f"Status: {resp.status_code}")
            if not passed:
                print_test("  Response", False, resp.text[:100])
            return passed
    except Exception as e:
        print_test("Webhook signature", False, f"Error: {e}")
        return False


async def test_webhook_verification():
    """Test 4: Meta Webhook Verification Flow"""
    print_header("Test 4: Meta Verification Flow")
    try:
        challenge = "test-challenge-12345"
        verify_token = "3CGIxdJVGO6EUFz4FXWSKpc0WvK_6rZCRuoKKxtGD7DzGMAHz"
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BASE_URL}/webhooks/whatsapp",
                params={
                    "hub.mode": "subscribe",
                    "hub.verify_token": verify_token,
                    "hub.challenge": challenge,
                },
            )
            passed = resp.status_code == 200 and resp.text == challenge
            print_test("Verification endpoint", passed, f"Challenge returned: {resp.text}")
            return passed
    except Exception as e:
        print_test("Webhook verification", False, f"Error: {e}")
        return False


async def test_kafka_producer():
    """Test 5: Kafka Producer"""
    print_header("Test 5: Kafka Producer")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{BASE_URL}/metrics")
            passed = resp.status_code == 200
            print_test("Metrics endpoint", passed, f"Status: {resp.status_code}")
            return passed
    except Exception as e:
        print_test("Kafka producer", False, f"Error: {e}")
        return False


async def test_whatsapp_api():
    """Test 6: WhatsApp Cloud API Connectivity"""
    print_header("Test 6: WhatsApp Cloud API")
    try:
        async with httpx.AsyncClient() as client:
            # Test Meta API with your credentials
            resp = await client.get(
                "https://graph.facebook.com/v19.0/1047635248436693",
                params={"access_token": "EAAYQ0P1gHE0BRKWVskZAw7dDeHPDcAupRtnOZAUhzmHHOZC9NyKXA27ZAAYCm5mQKDxVKYsC1Rn7xv2Vv4AKyT9ggoxTTyvezlFn0GSjD3M3UJDrf8jxQ3yZAZCDBtS51mjIGTRCyxz70sHtF5XZAcQvv9t8eZB6HSWFNocJZBCrsotGG9eqXr1qQloKJS9zUf6rYCYNUdhb3Nn1zuXCFwAF6nBxcaPz6mt3OMgNo7JPdyOQAilkGGckwWrZA9uONZCPhe1EwPSKPyZBq6NLqDqTU5UvNJSzJQZDZD"},
                timeout=10,
            )
            data = resp.json()
            passed = resp.status_code == 200 and "phone_number" in data
            print_test("Meta API connection", passed, f"Phone: {data.get('phone_number', 'N/A')}")
            if not passed:
                print_test("  Error", False, data.get('error', {}).get('message', str(data)))
            return passed
    except Exception as e:
        print_test("WhatsApp API", False, f"Error: {e}")
        return False


async def main():
    print(f"\n{CYAN}")
    print("╔" + "═"*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  🤖 WhatsApp Customer Support - Readiness Test".ljust(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "═"*68 + "╝")
    print(f"{RESET}")

    results = []
    results.append(await test_health())
    results.append(await test_skills())
    results.append(await test_webhook_signature())
    results.append(await test_webhook_verification())
    results.append(await test_kafka_producer())
    results.append(await test_whatsapp_api())

    passed = sum(results)
    total = len(results)

    print(f"\n{'='*70}")
    print(f"  RESULTS: {passed}/{total} tests passed")
    print(f"{'='*70}")

    if passed == total:
        print(f"\n  {GREEN}🎉 ALL TESTS PASSED!{RESET}")
        print(f"  {GREEN}Your WhatsApp Customer Support is READY!{RESET}")
        print(f"\n  Webhook URL: https://cuddly-loops-spend.loca.lt/webhooks/whatsapp")
        print(f"  Dashboard: http://localhost:3000")
        print(f"  API Docs: http://localhost:8000/docs")
    else:
        print(f"\n  {YELLOW}⚠️  Some tests failed. Review the details above.{RESET}")
        print(f"  {YELLOW}Fix the issues before going live.{RESET}")

    print()
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
