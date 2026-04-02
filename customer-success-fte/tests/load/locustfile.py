# ══════════════════════════════════════════════════════════════════════════════
# Load test — Customer Success Digital FTE
#
# Simulates 100 concurrent users sending a realistic mix of:
#   - Web form support submissions   (60%)
#   - WhatsApp inbound messages      (30%)
#   - Gmail push notifications       (10%)
#
# Usage:
#   pip install locust
#   locust -f tests/load/locustfile.py --host http://localhost:8000
#
# Headless CI run:
#   locust -f tests/load/locustfile.py \
#     --host http://localhost:8000 \
#     --headless -u 100 -r 10 --run-time 5m \
#     --html tests/load/report.html \
#     --csv tests/load/results
# ══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import random
import string
import time
import uuid

from locust import HttpUser, between, task


# ── Configuration ──────────────────────────────────────────────────────────────

INTERNAL_API_KEY = "test-internal-api-key"          # override with real key in env
WHATSAPP_APP_SECRET = "test-app-secret"              # override with real secret
WHATSAPP_VERIFY_TOKEN = "test-verify-token"


# ── Shared data pools ──────────────────────────────────────────────────────────

FIRST_NAMES = ["Alice", "Bob", "Carol", "Dave", "Eve", "Frank", "Grace", "Henry"]
LAST_NAMES  = ["Smith", "Jones", "Brown", "Taylor", "Wilson", "Davis", "Miller"]
COMPANIES   = ["Acme Corp", "Globex", "Initech", "Umbrella", "Hooli", "Pied Piper"]

SUBJECTS = [
    "Order not delivered",
    "Wrong item received",
    "Billing discrepancy",
    "Account access issue",
    "Product defect",
    "Subscription cancellation",
    "Technical support needed",
    "Refund request",
    "Shipping delay",
    "Feature inquiry",
]

MESSAGES = [
    "I placed an order three weeks ago and it still hasn't arrived. Please help.",
    "I was charged twice for my last order. Can you investigate?",
    "My account is locked and I can't reset my password.",
    "The product I received is defective. I need a replacement.",
    "How do I cancel my subscription?",
    "I need a receipt for my purchase for tax purposes.",
    "Can you update my shipping address for order #54321?",
    "The tracking number you provided isn't working.",
    "I'd like to upgrade my plan. What options are available?",
    "I received an email about a data breach. What should I do?",
]

WHATSAPP_PHONES = [
    "+15551000001", "+15551000002", "+15551000003",
    "+15551000004", "+15551000005", "+15551000006",
]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _random_email() -> str:
    name = "".join(random.choices(string.ascii_lowercase, k=6))
    domain = random.choice(["gmail.com", "yahoo.com", "example.com", "test.org"])
    return f"{name}@{domain}"


def _sign_whatsapp(body: bytes) -> str:
    sig = hmac.new(WHATSAPP_APP_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={sig}"


def _web_payload() -> dict:
    return {
        "name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
        "email": _random_email(),
        "phone": None,
        "company": random.choice(COMPANIES),
        "subject": random.choice(SUBJECTS),
        "message": random.choice(MESSAGES),
        "metadata": {"source": "load_test", "run_id": str(uuid.uuid4())},
    }


def _whatsapp_payload(phone: str, text: str) -> dict:
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "LOAD_TEST_ENTRY",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15550001234",
                                "phone_number_id": "LOAD_TEST_PHONE_ID",
                            },
                            "messages": [
                                {
                                    "from": phone,
                                    "id": f"wamid.{uuid.uuid4().hex}",
                                    "timestamp": str(int(time.time())),
                                    "type": "text",
                                    "text": {"body": text},
                                }
                            ],
                            "statuses": [],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }


def _gmail_push_payload() -> dict:
    data = {
        "historyId": str(random.randint(100000, 999999)),
        "emailAddress": _random_email(),
    }
    encoded = base64.b64encode(json.dumps(data).encode()).decode()
    return {
        "message": {
            "data": encoded,
            "messageId": f"pubsub-{uuid.uuid4().hex[:8]}",
            "publishTime": "2024-01-01T00:00:00Z",
            "attributes": {},
        },
        "subscription": "projects/load-test/subscriptions/gmail-push",
    }


# ════════════════════════════════════════════════════════════════════════════
# User behaviour
# ════════════════════════════════════════════════════════════════════════════

class SupportUser(HttpUser):
    """
    Simulates a customer contacting support via one of three channels.
    Weight distribution:  web 60% | whatsapp 30% | gmail 10%
    """

    wait_time = between(1, 5)   # seconds between tasks per user

    def on_start(self):
        """Each virtual user picks a random phone number (WhatsApp identity)."""
        self.phone = random.choice(WHATSAPP_PHONES)

    # ── Web form (60%) ────────────────────────────────────────────────────────

    @task(6)
    def submit_web_form(self):
        payload = _web_payload()
        with self.client.post(
            "/web/support",
            json=payload,
            headers={"X-API-Key": INTERNAL_API_KEY},
            catch_response=True,
            name="POST /web/support",
        ) as resp:
            if resp.status_code == 202:
                resp.success()
            elif resp.status_code == 429:
                resp.failure("Rate limited")
            else:
                resp.failure(f"Unexpected status: {resp.status_code}")

    # ── WhatsApp (30%) ────────────────────────────────────────────────────────

    @task(3)
    def send_whatsapp_message(self):
        text = random.choice(MESSAGES)
        body_dict = _whatsapp_payload(self.phone, text)
        body_bytes = json.dumps(body_dict).encode()

        with self.client.post(
            "/whatsapp",
            data=body_bytes,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": _sign_whatsapp(body_bytes),
            },
            catch_response=True,
            name="POST /whatsapp",
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            elif resp.status_code == 429:
                resp.failure("Rate limited")
            else:
                resp.failure(f"Unexpected status: {resp.status_code}")

    # ── Gmail push (10%) ──────────────────────────────────────────────────────

    @task(1)
    def trigger_gmail_push(self):
        payload = _gmail_push_payload()
        with self.client.post(
            "/gmail",
            json=payload,
            catch_response=True,
            name="POST /gmail",
        ) as resp:
            if resp.status_code in (200, 204):
                resp.success()
            elif resp.status_code == 429:
                resp.failure("Rate limited")
            else:
                resp.failure(f"Unexpected status: {resp.status_code}")


class MonitoringUser(HttpUser):
    """
    Simulates an ops dashboard polling health and metrics endpoints.
    Much lower weight than SupportUser — 1 monitor per ~20 support users.
    """

    wait_time = between(15, 30)
    weight = 1                   # 1 MonitoringUser for every 20 SupportUsers

    @task(3)
    def check_health(self):
        self.client.get("/health", name="GET /health")

    @task(2)
    def check_ready(self):
        self.client.get("/ready", name="GET /ready")

    @task(2)
    def fetch_prometheus_metrics(self):
        self.client.get("/metrics", name="GET /metrics")

    @task(1)
    def fetch_dashboard(self):
        self.client.get("/metrics/dashboard?time_range=1h", name="GET /metrics/dashboard")


# ── Custom event hooks for extended reporting ──────────────────────────────────

from locust import events

@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Log test parameters at startup."""
    print(
        "\n[Load Test] Customer Success Digital FTE\n"
        f"  Target users   : 100\n"
        f"  Spawn rate     : 10 users/s\n"
        f"  Channel mix    : web 60% | whatsapp 30% | gmail 10%\n"
        f"  Think time     : 1-5 s\n"
    )
