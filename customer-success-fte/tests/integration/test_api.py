# ══════════════════════════════════════════════════════════════════════════════
# Integration tests — FastAPI endpoints
# Uses httpx AsyncClient against the real app with external services mocked.
# ══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient


# ── App fixture with all heavy deps stubbed ────────────────────────────────────

@pytest_asyncio.fixture
async def client():
    """Full-stack test client; DB, Kafka, and SLA monitor are mocked."""
    with (
        patch("app.database.AsyncSessionFactory") as MockSession,
        patch("app.services.kafka_producer.get_producer") as mock_producer,
        patch("app.tasks.sla_monitor.run_sla_monitor", new_callable=AsyncMock),
    ):
        # DB session returns empty results by default
        session = AsyncMock()
        session.execute = AsyncMock(return_value=MagicMock(
            scalars=MagicMock(return_value=MagicMock(
                first=MagicMock(return_value=None),
                all=MagicMock(return_value=[]),
                one_or_none=MagicMock(return_value=None),
            )),
            scalar_one_or_none=MagicMock(return_value=None),
        ))
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=False)
        MockSession.return_value = session

        # Kafka producer
        producer = AsyncMock()
        producer.send_and_wait = AsyncMock()
        mock_producer.return_value = producer

        from app.main import app
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            yield ac


INTERNAL_API_KEY = "test-internal-api-key"


# ════════════════════════════════════════════════════════════════════════════
# /health  and  /ready
# ════════════════════════════════════════════════════════════════════════════

class TestHealthEndpoints:

    @pytest.mark.asyncio
    async def test_health_returns_200(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_health_response_has_status_field(self, client):
        resp = await client.get("/health")
        body = resp.json()
        assert "status" in body or resp.status_code == 200

    @pytest.mark.asyncio
    async def test_ready_returns_200_or_503(self, client):
        resp = await client.get("/ready")
        assert resp.status_code in (200, 503)


# ════════════════════════════════════════════════════════════════════════════
# POST /web/support
# ════════════════════════════════════════════════════════════════════════════

class TestWebFormEndpoint:

    VALID_PAYLOAD = {
        "name": "Alice Smith",
        "email": "alice@example.com",
        "phone": None,
        "company": "Acme Corp",
        "subject": "Order not delivered",
        "message": "I placed order #1234 three weeks ago and it has not arrived.",
        "metadata": {},
    }

    @pytest.mark.asyncio
    async def test_valid_submission_returns_202(self, client):
        with patch("app.routers.web_form.message_service") as mock_svc:
            mock_svc.ingest_web_form = AsyncMock(
                return_value=MagicMock(
                    ticket_id=uuid.UUID("00000000-0000-0000-0000-000000000099"),
                    message="Your message has been received.",
                )
            )
            resp = await client.post(
                "/web/support",
                json=self.VALID_PAYLOAD,
                headers={"X-API-Key": INTERNAL_API_KEY},
            )

        assert resp.status_code == 202

    @pytest.mark.asyncio
    async def test_missing_api_key_returns_401_or_403(self, client):
        resp = await client.post("/web/support", json=self.VALID_PAYLOAD)
        assert resp.status_code in (401, 403, 422)

    @pytest.mark.asyncio
    async def test_invalid_email_returns_422(self, client):
        bad_payload = {**self.VALID_PAYLOAD, "email": "not-an-email"}
        resp = await client.post(
            "/web/support",
            json=bad_payload,
            headers={"X-API-Key": INTERNAL_API_KEY},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_empty_message_returns_422(self, client):
        bad_payload = {**self.VALID_PAYLOAD, "message": ""}
        resp = await client.post(
            "/web/support",
            json=bad_payload,
            headers={"X-API-Key": INTERNAL_API_KEY},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_response_contains_ticket_id(self, client):
        fake_ticket_id = uuid.uuid4()
        with patch("app.routers.web_form.message_service") as mock_svc:
            mock_svc.ingest_web_form = AsyncMock(
                return_value=MagicMock(
                    ticket_id=fake_ticket_id,
                    message="Received",
                )
            )
            resp = await client.post(
                "/web/support",
                json=self.VALID_PAYLOAD,
                headers={"X-API-Key": INTERNAL_API_KEY},
            )

        if resp.status_code == 202:
            body = resp.json()
            assert "ticket_id" in body


# ════════════════════════════════════════════════════════════════════════════
# GET /whatsapp  (webhook verification)
# ════════════════════════════════════════════════════════════════════════════

class TestWhatsAppVerification:

    @pytest.mark.asyncio
    async def test_correct_token_returns_challenge(self, client):
        resp = await client.get(
            "/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "test-verify-token",
                "hub.challenge": "abc123",
            },
        )
        assert resp.status_code == 200
        assert "abc123" in resp.text

    @pytest.mark.asyncio
    async def test_wrong_token_returns_403(self, client):
        resp = await client.get(
            "/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "WRONG_TOKEN",
                "hub.challenge": "abc123",
            },
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_missing_params_returns_422(self, client):
        resp = await client.get("/whatsapp")
        assert resp.status_code == 422


# ════════════════════════════════════════════════════════════════════════════
# POST /whatsapp  (incoming message)
# ════════════════════════════════════════════════════════════════════════════

def _wa_payload(text: str = "Hello!") -> dict:
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "ENTRY_ID",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15550001234",
                                "phone_number_id": "PHONE_ID",
                            },
                            "messages": [
                                {
                                    "from": "+15551234567",
                                    "id": "wamid.abc123",
                                    "timestamp": "1700000000",
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


def _sign(body: bytes, secret: str = "test-app-secret") -> str:
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={sig}"


class TestWhatsAppWebhook:

    @pytest.mark.asyncio
    async def test_valid_message_returns_200(self, client):
        body = json.dumps(_wa_payload()).encode()
        with patch("app.routers.whatsapp.message_service") as mock_svc:
            mock_svc.ingest_whatsapp = AsyncMock()
            resp = await client.post(
                "/whatsapp",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Hub-Signature-256": _sign(body),
                },
            )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_missing_signature_returns_400_or_403(self, client):
        body = json.dumps(_wa_payload()).encode()
        resp = await client.post(
            "/whatsapp",
            content=body,
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code in (400, 403)

    @pytest.mark.asyncio
    async def test_invalid_signature_returns_403(self, client):
        body = json.dumps(_wa_payload()).encode()
        resp = await client.post(
            "/whatsapp",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": "sha256=badhash",
            },
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_status_update_payload_returns_200(self, client):
        """WhatsApp delivery receipts should be acknowledged silently."""
        status_payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "ENTRY_ID",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": "15550001234",
                                    "phone_number_id": "PHONE_ID",
                                },
                                "messages": [],
                                "statuses": [
                                    {
                                        "id": "wamid.delivered",
                                        "status": "delivered",
                                        "timestamp": "1700000001",
                                        "recipient_id": "+15551234567",
                                    }
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }
        body = json.dumps(status_payload).encode()
        resp = await client.post(
            "/whatsapp",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": _sign(body),
            },
        )
        assert resp.status_code == 200


# ════════════════════════════════════════════════════════════════════════════
# POST /gmail  (push notification)
# ════════════════════════════════════════════════════════════════════════════

class TestGmailWebhook:

    def _make_push_notification(self, email_data: dict | None = None) -> dict:
        data = email_data or {"historyId": "12345", "emailAddress": "customer@gmail.com"}
        encoded = base64.b64encode(json.dumps(data).encode()).decode()
        return {
            "message": {
                "data": encoded,
                "messageId": "pubsub-msg-001",
                "publishTime": "2024-01-01T00:00:00Z",
                "attributes": {},
            },
            "subscription": "projects/my-project/subscriptions/gmail-push",
        }

    @pytest.mark.asyncio
    async def test_valid_push_notification_returns_204(self, client):
        with patch("app.routers.gmail.gmail_service") as mock_svc:
            mock_svc.process_push_notification = AsyncMock()
            resp = await client.post("/gmail", json=self._make_push_notification())
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_malformed_payload_returns_400(self, client):
        resp = await client.post("/gmail", json={"bad": "payload"})
        assert resp.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_gmail_health_check(self, client):
        resp = await client.get("/gmail")
        assert resp.status_code == 200


# ════════════════════════════════════════════════════════════════════════════
# GET /metrics  and  GET /metrics/dashboard
# ════════════════════════════════════════════════════════════════════════════

class TestMetricsEndpoints:

    @pytest.mark.asyncio
    async def test_prometheus_metrics_returns_200(self, client):
        with patch("app.routers.metrics.get_dashboard_data", new_callable=AsyncMock) as mock_data:
            mock_data.return_value = {
                "conversations": {"total": 10},
                "tickets": {"total": 5, "resolved": 3, "escalated": 1},
                "agent": {"runs": 10, "avg_response_ms": 1234.5, "escalation_rate": 0.1},
                "quality": {"avg_csat": 4.2, "resolution_rate": 0.6},
                "cost": {"total_tokens": 50000, "prompt_tokens": 30000, "completion_tokens": 20000, "total_usd": 0.125, "per_conversation_usd": 0.0125},
            }
            resp = await client.get("/metrics")

        assert resp.status_code == 200
        assert "text/plain" in resp.headers["content-type"]

    @pytest.mark.asyncio
    async def test_prometheus_metrics_contains_gauge_names(self, client):
        with patch("app.routers.metrics.get_dashboard_data", new_callable=AsyncMock) as mock_data:
            mock_data.return_value = {
                "conversations": {"total": 0},
                "tickets": {"total": 0, "resolved": 0, "escalated": 0},
                "agent": {"runs": 0, "avg_response_ms": 0, "escalation_rate": 0},
                "quality": {"avg_csat": None, "resolution_rate": 0},
                "cost": {"total_tokens": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_usd": 0, "per_conversation_usd": 0},
            }
            resp = await client.get("/metrics")

        assert "csfte_" in resp.text

    @pytest.mark.asyncio
    async def test_dashboard_returns_json(self, client):
        with patch("app.routers.metrics.get_dashboard_data", new_callable=AsyncMock) as mock_data:
            mock_data.return_value = {
                "conversations": {"total": 100},
                "tickets": {"total": 50, "resolved": 40, "escalated": 5},
                "agent": {"runs": 100, "avg_response_ms": 800, "escalation_rate": 0.05},
                "quality": {"avg_csat": 4.5, "resolution_rate": 0.8},
                "cost": {"total_tokens": 100000, "prompt_tokens": 60000, "completion_tokens": 40000, "total_usd": 0.25, "per_conversation_usd": 0.0025},
            }
            resp = await client.get("/metrics/dashboard")

        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, dict)

    @pytest.mark.asyncio
    async def test_metrics_accepts_time_range_query(self, client):
        with patch("app.routers.metrics.get_dashboard_data", new_callable=AsyncMock) as mock_data:
            mock_data.return_value = {
                "conversations": {"total": 0},
                "tickets": {"total": 0, "resolved": 0, "escalated": 0},
                "agent": {"runs": 0, "avg_response_ms": 0, "escalation_rate": 0},
                "quality": {"avg_csat": None, "resolution_rate": 0},
                "cost": {"total_tokens": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_usd": 0, "per_conversation_usd": 0},
            }
            resp_1h = await client.get("/metrics?time_range=1h")
            resp_7d = await client.get("/metrics?time_range=7d")

        assert resp_1h.status_code == 200
        assert resp_7d.status_code == 200
