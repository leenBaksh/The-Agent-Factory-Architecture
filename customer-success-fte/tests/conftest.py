# ══════════════════════════════════════════════════════════════════════════════
# Shared pytest fixtures for Customer Success Digital FTE test suite.
# ══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations

import uuid
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# ── Scalar result helper ───────────────────────────────────────────────────────

class _FakeScalarsResult:
    """Mimics the object returned by session.scalars()."""

    def __init__(self, items: list):
        self._items = items

    def all(self):
        return self._items

    def first(self):
        return self._items[0] if self._items else None

    def one(self):
        if not self._items:
            raise Exception("No row found")
        return self._items[0]

    def one_or_none(self):
        return self._items[0] if self._items else None


class _FakeExecuteResult:
    """Mimics the object returned by session.execute()."""

    def __init__(self, items: list):
        self._items = items

    def scalars(self):
        return _FakeScalarsResult(self._items)

    def scalar_one_or_none(self):
        return self._items[0] if self._items else None

    def scalar(self):
        return self._items[0] if self._items else None


# ── Session fixture ────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def mock_session():
    """Async SQLAlchemy session stub."""
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.flush = AsyncMock()
    session.delete = AsyncMock()
    # Default execute → empty result; tests override with session.execute.return_value
    session.execute = AsyncMock(return_value=_FakeExecuteResult([]))
    return session


# ── Common UUIDs ───────────────────────────────────────────────────────────────

@pytest.fixture
def customer_id() -> uuid.UUID:
    return uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def conversation_id() -> uuid.UUID:
    return uuid.UUID("00000000-0000-0000-0000-000000000002")


@pytest.fixture
def message_id() -> uuid.UUID:
    return uuid.UUID("00000000-0000-0000-0000-000000000003")


@pytest.fixture
def ticket_id() -> uuid.UUID:
    return uuid.UUID("00000000-0000-0000-0000-000000000004")


# ── AgentContext fixture ───────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def agent_context(mock_session, customer_id, conversation_id, message_id):
    from app.agents.tools import AgentContext
    return AgentContext(
        session=mock_session,
        message_id=message_id,
        conversation_id=conversation_id,
        customer_id=customer_id,
        channel="web",
        customer_email="test@example.com",
        customer_phone=None,
        tickets_created=[],
        outbound_messages_created=[],
    )


# ── Kafka producer fixture ─────────────────────────────────────────────────────

@pytest.fixture
def mock_kafka_producer():
    producer = AsyncMock()
    producer.send_and_wait = AsyncMock()
    producer.start = AsyncMock()
    producer.stop = AsyncMock()
    return producer


# ── FastAPI test client ────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """HTTP test client with all external services mocked."""
    with (
        patch("app.database.AsyncSessionFactory"),
        patch("app.services.kafka_producer.get_producer"),
        patch("app.tasks.sla_monitor.run_sla_monitor", new_callable=AsyncMock),
    ):
        from app.main import app
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            yield ac


# ── Settings override ──────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def override_settings(monkeypatch):
    """Inject safe test values for all settings that touch external services."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-that-is-long-enough-32c")
    monkeypatch.setenv("INTERNAL_API_KEY", "test-internal-api-key")
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "test-verify-token")
    monkeypatch.setenv("WHATSAPP_APP_SECRET", "test-app-secret")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")


# ── Fake ORM row factories ─────────────────────────────────────────────────────

@pytest.fixture
def make_customer(customer_id):
    """Returns a factory that creates Customer-like objects."""
    from datetime import datetime, timezone

    def _factory(**overrides):
        row = MagicMock()
        row.id = overrides.get("id", customer_id)
        row.display_name = overrides.get("display_name", "Test Customer")
        row.email = overrides.get("email", "test@example.com")
        row.phone = overrides.get("phone", None)
        row.company = overrides.get("company", "Acme Corp")
        row.plan = overrides.get("plan", "pro")
        row.created_at = overrides.get("created_at", datetime.now(tz=timezone.utc))
        row.updated_at = overrides.get("updated_at", datetime.now(tz=timezone.utc))
        return row

    return _factory


@pytest.fixture
def make_ticket(ticket_id, conversation_id, customer_id):
    """Returns a factory that creates Ticket-like objects."""
    from datetime import datetime, timezone

    def _factory(**overrides):
        row = MagicMock()
        row.id = overrides.get("id", ticket_id)
        row.conversation_id = overrides.get("conversation_id", conversation_id)
        row.customer_id = overrides.get("customer_id", customer_id)
        row.subject = overrides.get("subject", "Test issue")
        row.description = overrides.get("description", "A test support issue")
        row.category = overrides.get("category", "general")
        row.status = overrides.get("status", "open")
        row.priority = overrides.get("priority", "medium")
        row.assigned_to = overrides.get("assigned_to", None)
        row.resolution = overrides.get("resolution", None)
        row.escalated_at = overrides.get("escalated_at", None)
        row.resolved_at = overrides.get("resolved_at", None)
        row.closed_at = overrides.get("closed_at", None)
        row.due_at = overrides.get("due_at", None)
        row.tags = overrides.get("tags", [])
        row.metadata_ = overrides.get("metadata_", {})
        row.created_at = overrides.get("created_at", datetime.now(tz=timezone.utc))
        row.updated_at = overrides.get("updated_at", datetime.now(tz=timezone.utc))
        return row

    return _factory


@pytest.fixture
def make_conversation(conversation_id, customer_id):
    """Returns a factory that creates Conversation-like objects."""
    from datetime import datetime, timezone

    def _factory(**overrides):
        row = MagicMock()
        row.id = overrides.get("id", conversation_id)
        row.customer_id = overrides.get("customer_id", customer_id)
        row.channel = overrides.get("channel", "web")
        row.status = overrides.get("status", "open")
        row.created_at = overrides.get("created_at", datetime.now(tz=timezone.utc))
        row.updated_at = overrides.get("updated_at", datetime.now(tz=timezone.utc))
        return row

    return _factory
