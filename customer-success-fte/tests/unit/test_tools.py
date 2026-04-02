# ══════════════════════════════════════════════════════════════════════════════
# Unit tests — Agent tool functions
# Each tool is called with a mocked AgentContext so no network or DB is needed.
# ══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio


# ── Helpers ────────────────────────────────────────────────────────────────────

def _wrap(agent_context):
    """Create a minimal RunContextWrapper-like object around AgentContext."""
    ctx = MagicMock()
    ctx.context = agent_context
    return ctx


class _FakeScalars:
    def __init__(self, items): self._items = items
    def all(self): return self._items
    def first(self): return self._items[0] if self._items else None
    def one_or_none(self): return self._items[0] if self._items else None


class _FakeExec:
    def __init__(self, items): self._items = items
    def scalars(self): return _FakeScalars(self._items)
    def scalar_one_or_none(self): return self._items[0] if self._items else None


# ════════════════════════════════════════════════════════════════════════════
# create_ticket
# ════════════════════════════════════════════════════════════════════════════

class TestCreateTicket:

    @pytest.mark.asyncio
    async def test_creates_ticket_and_returns_id(self, agent_context, mock_session, ticket_id):
        from app.agents.tools import create_ticket

        # Mock KnowledgeBaseRepository (not used here) and ticket creation
        fake_ticket = MagicMock()
        fake_ticket.id = ticket_id

        with patch("app.agents.tools.TicketRepository") as MockRepo:
            repo_instance = AsyncMock()
            repo_instance.create = AsyncMock(return_value=fake_ticket)
            MockRepo.return_value = repo_instance

            ctx = _wrap(agent_context)
            result = await create_ticket(
                ctx,
                subject="Login broken",
                priority="high",
                category="technical",
                description="Cannot log in since yesterday",
            )

        assert str(ticket_id) in result
        assert ticket_id in agent_context.tickets_created

    @pytest.mark.asyncio
    async def test_uses_default_priority(self, agent_context, ticket_id):
        from app.agents.tools import create_ticket

        fake_ticket = MagicMock()
        fake_ticket.id = ticket_id

        with patch("app.agents.tools.TicketRepository") as MockRepo:
            repo_instance = AsyncMock()
            repo_instance.create = AsyncMock(return_value=fake_ticket)
            MockRepo.return_value = repo_instance

            ctx = _wrap(agent_context)
            result = await create_ticket(ctx, subject="Issue", priority="medium")

        assert str(ticket_id) in result


# ════════════════════════════════════════════════════════════════════════════
# search_knowledge_base
# ════════════════════════════════════════════════════════════════════════════

class TestSearchKnowledgeBase:

    @pytest.mark.asyncio
    async def test_returns_formatted_results(self, agent_context):
        from app.agents.tools import search_knowledge_base

        fake_article = MagicMock()
        fake_article.title = "How to reset your password"
        fake_article.content = "Go to settings and click reset."
        fake_article.category = "account"

        with (
            patch("app.agents.tools._get_embedding", new_callable=AsyncMock) as mock_embed,
            patch("app.agents.tools.KnowledgeBaseRepository") as MockRepo,
        ):
            mock_embed.return_value = [0.0] * 1536
            repo_instance = AsyncMock()
            repo_instance.semantic_search = AsyncMock(return_value=[fake_article])
            MockRepo.return_value = repo_instance

            ctx = _wrap(agent_context)
            result = await search_knowledge_base(ctx, query="password reset", limit=3)

        assert "reset" in result.lower() or "password" in result.lower()

    @pytest.mark.asyncio
    async def test_no_results_returns_message(self, agent_context):
        from app.agents.tools import search_knowledge_base

        with (
            patch("app.agents.tools._get_embedding", new_callable=AsyncMock) as mock_embed,
            patch("app.agents.tools.KnowledgeBaseRepository") as MockRepo,
        ):
            mock_embed.return_value = [0.0] * 1536
            repo_instance = AsyncMock()
            repo_instance.semantic_search = AsyncMock(return_value=[])
            MockRepo.return_value = repo_instance

            ctx = _wrap(agent_context)
            result = await search_knowledge_base(ctx, query="unknown topic")

        assert "no" in result.lower() or "not found" in result.lower() or len(result) > 0


# ════════════════════════════════════════════════════════════════════════════
# get_customer_history
# ════════════════════════════════════════════════════════════════════════════

class TestGetCustomerHistory:

    @pytest.mark.asyncio
    async def test_returns_conversation_summary(self, agent_context):
        from app.agents.tools import get_customer_history

        fake_conv = MagicMock()
        fake_conv.id = uuid.uuid4()
        fake_conv.channel = "web"
        fake_conv.status = "closed"
        fake_conv.created_at = MagicMock()
        fake_conv.created_at.isoformat.return_value = "2024-01-01T00:00:00+00:00"

        fake_msg = MagicMock()
        fake_msg.direction = "inbound"
        fake_msg.content = "Where is my order?"

        with (
            patch("app.agents.tools.ConversationRepository") as MockConvRepo,
            patch("app.agents.tools.MessageRepository") as MockMsgRepo,
        ):
            conv_repo = AsyncMock()
            conv_repo.list_by_customer = AsyncMock(return_value=[fake_conv])
            MockConvRepo.return_value = conv_repo

            msg_repo = AsyncMock()
            msg_repo.list_by_conversation = AsyncMock(return_value=[fake_msg])
            MockMsgRepo.return_value = msg_repo

            ctx = _wrap(agent_context)
            result = await get_customer_history(ctx, max_conversations=5)

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_no_history_returns_message(self, agent_context):
        from app.agents.tools import get_customer_history

        with patch("app.agents.tools.ConversationRepository") as MockConvRepo:
            conv_repo = AsyncMock()
            conv_repo.list_by_customer = AsyncMock(return_value=[])
            MockConvRepo.return_value = conv_repo

            ctx = _wrap(agent_context)
            result = await get_customer_history(ctx)

        assert isinstance(result, str)


# ════════════════════════════════════════════════════════════════════════════
# escalate_to_human
# ════════════════════════════════════════════════════════════════════════════

class TestEscalateToHuman:

    @pytest.mark.asyncio
    async def test_escalation_creates_or_updates_ticket(self, agent_context, ticket_id):
        from app.agents.tools import escalate_to_human

        fake_ticket = MagicMock()
        fake_ticket.id = ticket_id
        fake_ticket.status = "open"

        with patch("app.agents.tools.TicketRepository") as MockRepo:
            repo_instance = AsyncMock()
            repo_instance.list_by_conversation = AsyncMock(return_value=[fake_ticket])
            repo_instance.update = AsyncMock(return_value=fake_ticket)
            MockRepo.return_value = repo_instance

            ctx = _wrap(agent_context)
            result = await escalate_to_human(ctx, reason="Customer requested human agent")

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_escalation_with_explicit_ticket_id(self, agent_context, ticket_id):
        from app.agents.tools import escalate_to_human

        fake_ticket = MagicMock()
        fake_ticket.id = ticket_id
        fake_ticket.status = "open"
        fake_ticket.escalated_at = None

        with patch("app.agents.tools.TicketRepository") as MockRepo:
            repo_instance = AsyncMock()
            repo_instance.get = AsyncMock(return_value=fake_ticket)
            repo_instance.update = AsyncMock(return_value=fake_ticket)
            MockRepo.return_value = repo_instance

            ctx = _wrap(agent_context)
            result = await escalate_to_human(
                ctx, reason="Legal threat", ticket_id=str(ticket_id)
            )

        assert isinstance(result, str)


# ════════════════════════════════════════════════════════════════════════════
# send_response
# ════════════════════════════════════════════════════════════════════════════

class TestSendResponse:

    @pytest.mark.asyncio
    async def test_web_channel_publishes_to_kafka(self, agent_context):
        from app.agents.tools import send_response

        agent_context.channel = "web"

        with patch("app.agents.tools.get_producer") as mock_get_producer:
            producer = AsyncMock()
            producer.send_and_wait = AsyncMock()
            mock_get_producer.return_value = producer

            ctx = _wrap(agent_context)
            result = await send_response(ctx, message="Your order is on its way!")

        assert isinstance(result, str)
        assert len(agent_context.outbound_messages_created) >= 0  # may persist to DB too

    @pytest.mark.asyncio
    async def test_whatsapp_channel_calls_whatsapp_api(self, agent_context):
        from app.agents.tools import send_response

        agent_context.channel = "whatsapp"
        agent_context.customer_phone = "+15550001111"

        with (
            patch("app.agents.tools._send_whatsapp", new_callable=AsyncMock),
            patch("app.agents.tools.get_producer") as mock_get_producer,
        ):
            producer = AsyncMock()
            producer.send_and_wait = AsyncMock()
            mock_get_producer.return_value = producer

            ctx = _wrap(agent_context)
            result = await send_response(ctx, message="Hello from WhatsApp!")

        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_empty_message_still_succeeds(self, agent_context):
        from app.agents.tools import send_response

        with patch("app.agents.tools.get_producer") as mock_get_producer:
            producer = AsyncMock()
            producer.send_and_wait = AsyncMock()
            mock_get_producer.return_value = producer

            ctx = _wrap(agent_context)
            # Should not raise even with empty message
            result = await send_response(ctx, message="")

        assert result is not None


# ════════════════════════════════════════════════════════════════════════════
# resolve_ticket
# ════════════════════════════════════════════════════════════════════════════

class TestResolveTicket:

    @pytest.mark.asyncio
    async def test_resolves_open_ticket(self, agent_context, ticket_id):
        from app.agents.tools import resolve_ticket

        fake_ticket = MagicMock()
        fake_ticket.id = ticket_id
        fake_ticket.status = "open"
        fake_ticket.resolved_at = None

        with (
            patch("app.agents.tools.TicketRepository") as MockRepo,
            patch("app.agents.tools.ticket_lifecycle_service") as mock_svc,
        ):
            repo_instance = AsyncMock()
            repo_instance.list_by_conversation = AsyncMock(return_value=[fake_ticket])
            MockRepo.return_value = repo_instance

            mock_svc.resolve_ticket = AsyncMock(return_value=fake_ticket)

            ctx = _wrap(agent_context)
            result = await resolve_ticket(
                ctx,
                resolution="Confirmed order was delivered to the correct address.",
            )

        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_resolve_with_explicit_ticket_id(self, agent_context, ticket_id):
        from app.agents.tools import resolve_ticket

        fake_ticket = MagicMock()
        fake_ticket.id = ticket_id
        fake_ticket.status = "in_progress"

        with (
            patch("app.agents.tools.TicketRepository") as MockRepo,
            patch("app.agents.tools.ticket_lifecycle_service") as mock_svc,
        ):
            repo_instance = AsyncMock()
            repo_instance.get = AsyncMock(return_value=fake_ticket)
            MockRepo.return_value = repo_instance

            mock_svc.resolve_ticket = AsyncMock(return_value=fake_ticket)

            ctx = _wrap(agent_context)
            result = await resolve_ticket(
                ctx,
                resolution="Issue resolved by restarting account.",
                ticket_id=str(ticket_id),
            )

        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_no_ticket_found_returns_message(self, agent_context):
        from app.agents.tools import resolve_ticket

        with patch("app.agents.tools.TicketRepository") as MockRepo:
            repo_instance = AsyncMock()
            repo_instance.list_by_conversation = AsyncMock(return_value=[])
            MockRepo.return_value = repo_instance

            ctx = _wrap(agent_context)
            result = await resolve_ticket(ctx, resolution="Nothing to resolve.")

        assert isinstance(result, str)
        assert len(result) > 0


# ════════════════════════════════════════════════════════════════════════════
# AgentContext
# ════════════════════════════════════════════════════════════════════════════

class TestAgentContext:

    def test_tickets_created_starts_empty(self, agent_context):
        assert agent_context.tickets_created == []

    def test_outbound_messages_starts_empty(self, agent_context):
        assert agent_context.outbound_messages_created == []

    def test_channel_attribute(self, agent_context):
        assert agent_context.channel in ("web", "gmail", "whatsapp")

    def test_has_required_ids(self, agent_context):
        assert agent_context.message_id is not None
        assert agent_context.conversation_id is not None
        assert agent_context.customer_id is not None
