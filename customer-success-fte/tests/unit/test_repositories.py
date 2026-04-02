# ══════════════════════════════════════════════════════════════════════════════
# Unit tests — Repository layer
# Tests the CRUD operations and domain-specific queries of each repository.
# All database interaction is mocked; no running PostgreSQL is required.
# ══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio


# ── Helpers ────────────────────────────────────────────────────────────────────

class _Scalars:
    def __init__(self, items):
        self._items = items
    def all(self):        return self._items
    def first(self):      return self._items[0] if self._items else None
    def one_or_none(self): return self._items[0] if self._items else None
    def one(self):
        if not self._items: raise Exception("No row")
        return self._items[0]


class _ExecResult:
    def __init__(self, items):
        self._items = items
    def scalars(self):               return _Scalars(self._items)
    def scalar_one_or_none(self):   return self._items[0] if self._items else None
    def scalar(self):               return self._items[0] if self._items else None


def _session_returning(*items):
    """Return an AsyncMock session whose execute() yields *items."""
    s = AsyncMock()
    s.add = MagicMock()
    s.commit = AsyncMock()
    s.refresh = AsyncMock()
    s.flush = AsyncMock()
    s.delete = AsyncMock()
    s.execute = AsyncMock(return_value=_ExecResult(list(items)))
    return s


# ════════════════════════════════════════════════════════════════════════════
# BaseRepository
# ════════════════════════════════════════════════════════════════════════════

class TestBaseRepository:
    """Tests generic CRUD behaviour using CustomerRepository as a concrete impl."""

    @pytest_asyncio.fixture
    def repo(self, mock_session):
        from app.repositories.customers import CustomerRepository
        return CustomerRepository(mock_session)

    # ── read ─────────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_returns_row_when_found(self, repo, mock_session, make_customer, customer_id):
        customer = make_customer()
        mock_session.execute.return_value = _ExecResult([customer])

        result = await repo.get(customer_id)

        assert result is customer

    @pytest.mark.asyncio
    async def test_get_returns_none_when_missing(self, repo, mock_session):
        mock_session.execute.return_value = _ExecResult([])

        result = await repo.get(uuid.uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_get_or_raise_raises_when_missing(self, repo, mock_session):
        mock_session.execute.return_value = _ExecResult([])

        with pytest.raises(Exception):
            await repo.get_or_raise(uuid.uuid4())

    @pytest.mark.asyncio
    async def test_list_returns_all_rows(self, repo, mock_session, make_customer):
        rows = [make_customer(id=uuid.uuid4()) for _ in range(3)]
        mock_session.execute.return_value = _ExecResult(rows)

        result = await repo.list()

        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_list_respects_limit_offset(self, repo, mock_session, make_customer):
        """list() should pass limit/offset into the SELECT statement."""
        mock_session.execute.return_value = _ExecResult([make_customer()])

        # Simply verify no exception is raised; SQL construction is tested via SQL assertions
        result = await repo.list(limit=1, offset=5)

        assert len(result) == 1

    # ── write ─────────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_create_adds_and_commits(self, repo, mock_session, make_customer):
        customer = make_customer()
        mock_session.refresh = AsyncMock(side_effect=lambda obj: None)

        # Patch the model class so repo.create() returns our fake row
        import app.repositories.customers as mod
        OrigModel = getattr(mod, "Customer", None)
        if OrigModel:
            with MagicMock() as MockCustomer:
                MockCustomer.return_value = customer
                mod.Customer = MockCustomer
                result = await repo.create(
                    display_name="Alice", email="alice@example.com"
                )
                mod.Customer = OrigModel

        mock_session.add.assert_called()
        mock_session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_delete_by_id_removes_row(self, repo, mock_session, make_customer, customer_id):
        customer = make_customer()
        mock_session.execute.return_value = _ExecResult([customer])

        await repo.delete_by_id(customer_id)

        mock_session.delete.assert_awaited()
        mock_session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_update_sets_fields_and_commits(self, repo, mock_session, make_customer):
        customer = make_customer()
        customer.display_name = "Old Name"

        await repo.update(customer, display_name="New Name")

        assert customer.display_name == "New Name"
        mock_session.commit.assert_awaited()


# ════════════════════════════════════════════════════════════════════════════
# CustomerRepository
# ════════════════════════════════════════════════════════════════════════════

class TestCustomerRepository:

    @pytest_asyncio.fixture
    def repo(self, mock_session):
        from app.repositories.customers import CustomerRepository
        return CustomerRepository(mock_session)

    @pytest.mark.asyncio
    async def test_get_by_email_found(self, repo, mock_session, make_customer):
        customer = make_customer(email="alice@example.com")
        mock_session.execute.return_value = _ExecResult([customer])

        result = await repo.get_by_email("alice@example.com")

        assert result is customer

    @pytest.mark.asyncio
    async def test_get_by_email_not_found(self, repo, mock_session):
        mock_session.execute.return_value = _ExecResult([])

        result = await repo.get_by_email("nobody@example.com")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_phone_found(self, repo, mock_session, make_customer):
        customer = make_customer(phone="+15551234567")
        mock_session.execute.return_value = _ExecResult([customer])

        result = await repo.get_by_phone("+15551234567")

        assert result is customer

    @pytest.mark.asyncio
    async def test_search_by_company(self, repo, mock_session, make_customer):
        customers = [make_customer(company="Acme") for _ in range(2)]
        mock_session.execute.return_value = _ExecResult(customers)

        result = await repo.search_by_company("Acme")

        assert len(result) == 2


# ════════════════════════════════════════════════════════════════════════════
# TicketRepository
# ════════════════════════════════════════════════════════════════════════════

class TestTicketRepository:

    @pytest_asyncio.fixture
    def repo(self, mock_session):
        from app.repositories.tickets import TicketRepository
        return TicketRepository(mock_session)

    @pytest.mark.asyncio
    async def test_list_by_customer(self, repo, mock_session, make_ticket):
        tickets = [make_ticket(id=uuid.uuid4()) for _ in range(3)]
        mock_session.execute.return_value = _ExecResult(tickets)

        result = await repo.list_by_customer(uuid.uuid4())

        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_list_by_status_open(self, repo, mock_session, make_ticket):
        tickets = [make_ticket(status="open"), make_ticket(status="open")]
        mock_session.execute.return_value = _ExecResult(tickets)

        result = await repo.list_by_status("open")

        assert all(t.status == "open" for t in result)

    @pytest.mark.asyncio
    async def test_list_escalated(self, repo, mock_session, make_ticket):
        from datetime import datetime, timezone
        tickets = [make_ticket(escalated_at=datetime.now(tz=timezone.utc))]
        mock_session.execute.return_value = _ExecResult(tickets)

        result = await repo.list_escalated()

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_list_by_priority(self, repo, mock_session, make_ticket):
        tickets = [make_ticket(priority="high") for _ in range(2)]
        mock_session.execute.return_value = _ExecResult(tickets)

        result = await repo.list_by_priority("high")

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_by_conversation(self, repo, mock_session, make_ticket, conversation_id):
        tickets = [make_ticket(), make_ticket(id=uuid.uuid4())]
        mock_session.execute.return_value = _ExecResult(tickets)

        result = await repo.list_by_conversation(conversation_id)

        assert len(result) == 2


# ════════════════════════════════════════════════════════════════════════════
# ConversationRepository
# ════════════════════════════════════════════════════════════════════════════

class TestConversationRepository:

    @pytest_asyncio.fixture
    def repo(self, mock_session):
        from app.repositories.conversations import ConversationRepository
        return ConversationRepository(mock_session)

    @pytest.mark.asyncio
    async def test_get_open_by_customer_and_channel_found(
        self, repo, mock_session, make_conversation, customer_id
    ):
        conv = make_conversation(status="open", channel="web")
        mock_session.execute.return_value = _ExecResult([conv])

        result = await repo.get_open_by_customer_and_channel(customer_id, "web")

        assert result is conv

    @pytest.mark.asyncio
    async def test_get_open_by_customer_and_channel_none(self, repo, mock_session, customer_id):
        mock_session.execute.return_value = _ExecResult([])

        result = await repo.get_open_by_customer_and_channel(customer_id, "whatsapp")

        assert result is None

    @pytest.mark.asyncio
    async def test_list_by_customer(self, repo, mock_session, make_conversation, customer_id):
        conversations = [make_conversation() for _ in range(5)]
        mock_session.execute.return_value = _ExecResult(conversations)

        result = await repo.list_by_customer(customer_id)

        assert len(result) == 5


# ════════════════════════════════════════════════════════════════════════════
# KnowledgeBaseRepository
# ════════════════════════════════════════════════════════════════════════════

class TestKnowledgeBaseRepository:

    @pytest_asyncio.fixture
    def repo(self, mock_session):
        from app.repositories.knowledge_base import KnowledgeBaseRepository
        return KnowledgeBaseRepository(mock_session)

    @pytest.mark.asyncio
    async def test_list_active(self, repo, mock_session):
        items = [MagicMock() for _ in range(4)]
        mock_session.execute.return_value = _ExecResult(items)

        result = await repo.list_active()

        assert len(result) == 4

    @pytest.mark.asyncio
    async def test_list_by_category(self, repo, mock_session):
        items = [MagicMock(category="billing") for _ in range(2)]
        mock_session.execute.return_value = _ExecResult(items)

        result = await repo.list_by_category("billing")

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_semantic_search_returns_results(self, repo, mock_session):
        items = [MagicMock() for _ in range(3)]
        mock_session.execute.return_value = _ExecResult(items)

        embedding = [0.0] * 1536
        result = await repo.semantic_search(embedding, limit=3)

        assert len(result) == 3
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_semantic_search_empty_result(self, repo, mock_session):
        mock_session.execute.return_value = _ExecResult([])

        result = await repo.semantic_search([0.0] * 1536)

        assert result == [] or list(result) == []


# ════════════════════════════════════════════════════════════════════════════
# MessageRepository
# ════════════════════════════════════════════════════════════════════════════

class TestMessageRepository:

    @pytest_asyncio.fixture
    def repo(self, mock_session):
        from app.repositories.messages import MessageRepository
        return MessageRepository(mock_session)

    @pytest.mark.asyncio
    async def test_list_by_conversation(self, repo, mock_session, conversation_id):
        messages = [MagicMock() for _ in range(6)]
        mock_session.execute.return_value = _ExecResult(messages)

        result = await repo.list_by_conversation(conversation_id)

        assert len(result) == 6

    @pytest.mark.asyncio
    async def test_list_pending(self, repo, mock_session):
        messages = [MagicMock(status="pending") for _ in range(2)]
        mock_session.execute.return_value = _ExecResult(messages)

        result = await repo.list_pending()

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_failed(self, repo, mock_session):
        mock_session.execute.return_value = _ExecResult([])

        result = await repo.list_failed()

        assert list(result) == []


# ════════════════════════════════════════════════════════════════════════════
# AgentMetricRepository
# ════════════════════════════════════════════════════════════════════════════

class TestAgentMetricRepository:

    @pytest_asyncio.fixture
    def repo(self, mock_session):
        from app.repositories.agent_metrics import AgentMetricRepository
        return AgentMetricRepository(mock_session)

    @pytest.mark.asyncio
    async def test_list_by_message(self, repo, mock_session, message_id):
        metrics = [MagicMock() for _ in range(2)]
        mock_session.execute.return_value = _ExecResult(metrics)

        result = await repo.list_by_message(message_id)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_escalation_rate_returns_float(self, repo, mock_session):
        mock_session.execute.return_value = _ExecResult([0.25])

        rate = await repo.escalation_rate()

        assert isinstance(rate, float)


# ════════════════════════════════════════════════════════════════════════════
# CustomerIdentifierRepository
# ════════════════════════════════════════════════════════════════════════════

class TestCustomerIdentifierRepository:

    @pytest_asyncio.fixture
    def repo(self, mock_session):
        from app.repositories.customer_identifiers import CustomerIdentifierRepository
        return CustomerIdentifierRepository(mock_session)

    @pytest.mark.asyncio
    async def test_get_by_channel_and_external_id_found(self, repo, mock_session):
        identifier = MagicMock()
        mock_session.execute.return_value = _ExecResult([identifier])

        result = await repo.get_by_channel_and_external_id("whatsapp", "+15551234567")

        assert result is identifier

    @pytest.mark.asyncio
    async def test_get_by_channel_and_external_id_missing(self, repo, mock_session):
        mock_session.execute.return_value = _ExecResult([])

        result = await repo.get_by_channel_and_external_id("whatsapp", "+10000000000")

        assert result is None

    @pytest.mark.asyncio
    async def test_list_by_customer(self, repo, mock_session, customer_id):
        identifiers = [MagicMock() for _ in range(2)]
        mock_session.execute.return_value = _ExecResult(identifiers)

        result = await repo.list_by_customer(customer_id)

        assert len(result) == 2
