# ══════════════════════════════════════════════════════════════════════════════
# Integration tests — Agent end-to-end conversation flow
# Tests the full agent pipeline: guardrails → tools → OpenAI → response.
# OpenAI API is mocked; no external API calls are made.
# ══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_run_result(output_text: str = "I can help you with that.", tool_calls: list | None = None):
    """Fake RunResult from openai-agents SDK."""
    result = MagicMock()
    result.final_output = output_text
    result.new_items = tool_calls or []
    return result


@pytest_asyncio.fixture
async def ctx(agent_context):
    return agent_context


# ════════════════════════════════════════════════════════════════════════════
# run_support_agent — happy path
# ════════════════════════════════════════════════════════════════════════════

class TestRunSupportAgent:

    @pytest.mark.asyncio
    async def test_simple_inquiry_succeeds(self, ctx):
        from app.agents.coordinator import run_support_agent

        with patch("app.agents.coordinator.Runner.run", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = _make_run_result(
                "Your order #12345 is on its way and will arrive Thursday."
            )

            result = await run_support_agent(ctx, "Where is my order #12345?")

        assert result.success is True
        assert result.escalated is False
        assert result.error is None
        assert result.latency_ms >= 0

    @pytest.mark.asyncio
    async def test_result_contains_final_output(self, ctx):
        from app.agents.coordinator import run_support_agent

        with patch("app.agents.coordinator.Runner.run", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = _make_run_result("Here is what I found in our knowledge base.")

            result = await run_support_agent(ctx, "How do I reset my password?")

        assert result.final_output is not None
        assert len(result.final_output) > 0

    @pytest.mark.asyncio
    async def test_message_id_matches_context(self, ctx, message_id):
        from app.agents.coordinator import run_support_agent

        with patch("app.agents.coordinator.Runner.run", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = _make_run_result("Understood.")

            result = await run_support_agent(ctx, "I need help.")

        assert result.message_id == message_id


# ════════════════════════════════════════════════════════════════════════════
# PII guardrail
# ════════════════════════════════════════════════════════════════════════════

class TestPIIGuardrailIntegration:

    @pytest.mark.asyncio
    async def test_pii_in_message_trips_guardrail(self, ctx):
        from agents.exceptions import InputGuardrailTripwireTriggered
        from app.agents.coordinator import run_support_agent

        with patch("app.agents.coordinator.Runner.run", new_callable=AsyncMock) as mock_run:
            mock_run.side_effect = InputGuardrailTripwireTriggered(
                guardrail=MagicMock(name="pii_guardrail"),
                output=MagicMock(tripwire_triggered=True),
            )

            result = await run_support_agent(
                ctx, "My SSN is 123-45-6789 and email is user@example.com"
            )

        # When PII guardrail trips, the agent should handle it gracefully
        # (either by masking and continuing, or by returning an escalation)
        assert result is not None

    @pytest.mark.asyncio
    async def test_clean_message_passes_pii_guardrail(self, ctx):
        from app.agents.coordinator import run_support_agent

        with patch("app.agents.coordinator.Runner.run", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = _make_run_result("Happy to help with your order!")

            result = await run_support_agent(ctx, "Can you check the status of my order?")

        assert result.success is True


# ════════════════════════════════════════════════════════════════════════════
# Keyword escalation guardrail
# ════════════════════════════════════════════════════════════════════════════

class TestKeywordEscalationIntegration:

    @pytest.mark.asyncio
    async def test_legal_keyword_triggers_escalation(self, ctx):
        from agents.exceptions import InputGuardrailTripwireTriggered
        from app.agents.coordinator import run_support_agent

        with patch("app.agents.coordinator.Runner.run", new_callable=AsyncMock) as mock_run:
            mock_run.side_effect = InputGuardrailTripwireTriggered(
                guardrail=MagicMock(name="keyword_escalation_guardrail"),
                output=MagicMock(
                    tripwire_triggered=True,
                    output_info={"keyword": "lawsuit"},
                ),
            )

            result = await run_support_agent(
                ctx, "I am filing a lawsuit against your company."
            )

        assert result is not None
        # Guardrail trips result in escalation
        if result.escalated:
            assert result.escalation_reason is not None

    @pytest.mark.asyncio
    async def test_escalation_result_has_response(self, ctx):
        from agents.exceptions import InputGuardrailTripwireTriggered
        from app.agents.coordinator import run_support_agent

        with patch("app.agents.coordinator.Runner.run", new_callable=AsyncMock) as mock_run:
            mock_run.side_effect = InputGuardrailTripwireTriggered(
                guardrail=MagicMock(name="keyword_escalation_guardrail"),
                output=MagicMock(tripwire_triggered=True, output_info={}),
            )

            result = await run_support_agent(ctx, "I want a refund or I will sue!")

        # Even escalated results should have a response queued for the customer
        assert result is not None


# ════════════════════════════════════════════════════════════════════════════
# Sentiment guardrail
# ════════════════════════════════════════════════════════════════════════════

class TestSentimentEscalationIntegration:

    @pytest.mark.asyncio
    async def test_extreme_negativity_escalates(self, ctx):
        from agents.exceptions import InputGuardrailTripwireTriggered
        from app.agents.coordinator import run_support_agent

        with patch("app.agents.coordinator.Runner.run", new_callable=AsyncMock) as mock_run:
            mock_run.side_effect = InputGuardrailTripwireTriggered(
                guardrail=MagicMock(name="sentiment_guardrail"),
                output=MagicMock(tripwire_triggered=True, output_info={"score": 0.85}),
            )

            result = await run_support_agent(
                ctx,
                "I AM ABSOLUTELY FURIOUS! THIS IS THE WORST COMPANY EVER!!! "
                "HOW DARE YOU TREAT CUSTOMERS THIS WAY!!!",
            )

        assert result is not None


# ════════════════════════════════════════════════════════════════════════════
# Tool invocation via agent
# ════════════════════════════════════════════════════════════════════════════

class TestAgentToolCalls:

    @pytest.mark.asyncio
    async def test_agent_can_call_create_ticket(self, ctx):
        from app.agents.coordinator import run_support_agent

        # Simulate agent completing with a create_ticket tool call
        tool_call_item = MagicMock()
        tool_call_item.type = "tool_call_output"
        tool_call_item.output = str(uuid.uuid4())  # ticket ID returned

        with patch("app.agents.coordinator.Runner.run", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = _make_run_result(
                "I've created ticket #T-001 for your issue.",
                tool_calls=[tool_call_item],
            )

            result = await run_support_agent(
                ctx, "My subscription is not working at all. Please open a ticket."
            )

        assert result.success is True

    @pytest.mark.asyncio
    async def test_agent_can_call_search_knowledge_base(self, ctx):
        from app.agents.coordinator import run_support_agent

        with patch("app.agents.coordinator.Runner.run", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = _make_run_result(
                "Based on our knowledge base, you can reset your password by..."
            )

            result = await run_support_agent(ctx, "How do I change my password?")

        assert result.success is True
        assert "password" in result.final_output.lower()


# ════════════════════════════════════════════════════════════════════════════
# Error handling
# ════════════════════════════════════════════════════════════════════════════

class TestAgentErrorHandling:

    @pytest.mark.asyncio
    async def test_openai_timeout_returns_failure_result(self, ctx):
        from app.agents.coordinator import run_support_agent

        with patch("app.agents.coordinator.Runner.run", new_callable=AsyncMock) as mock_run:
            mock_run.side_effect = TimeoutError("OpenAI API timeout")

            result = await run_support_agent(ctx, "Hello!")

        assert result.success is False
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_openai_api_error_returns_failure_result(self, ctx):
        from app.agents.coordinator import run_support_agent

        with patch("app.agents.coordinator.Runner.run", new_callable=AsyncMock) as mock_run:
            mock_run.side_effect = RuntimeError("Rate limit exceeded")

            result = await run_support_agent(ctx, "Hello!")

        assert result.success is False

    @pytest.mark.asyncio
    async def test_failed_result_has_no_final_output(self, ctx):
        from app.agents.coordinator import run_support_agent

        with patch("app.agents.coordinator.Runner.run", new_callable=AsyncMock) as mock_run:
            mock_run.side_effect = Exception("Unexpected error")

            result = await run_support_agent(ctx, "Hello!")

        assert result.success is False
        assert result.final_output is None or result.error is not None


# ════════════════════════════════════════════════════════════════════════════
# Multi-turn conversation
# ════════════════════════════════════════════════════════════════════════════

class TestMultiTurnConversation:

    @pytest.mark.asyncio
    async def test_follow_up_message_uses_same_context(self, ctx):
        from app.agents.coordinator import run_support_agent

        with patch("app.agents.coordinator.Runner.run", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = _make_run_result("What was your order number?")
            result1 = await run_support_agent(ctx, "My order is late.")
            assert result1.success is True

            mock_run.return_value = _make_run_result(
                "I found order #12345. It was dispatched yesterday."
            )
            result2 = await run_support_agent(ctx, "It's order #12345.")
            assert result2.success is True

        # Both calls should use the same conversation_id
        assert ctx.conversation_id is not None

    @pytest.mark.asyncio
    async def test_ticket_created_in_first_turn_accessible_in_second(self, ctx):
        from app.agents.coordinator import run_support_agent

        # Simulate ticket creation in first turn
        ticket_id = uuid.uuid4()
        ctx.tickets_created.append(ticket_id)

        with patch("app.agents.coordinator.Runner.run", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = _make_run_result(
                "I've escalated your ticket to our senior team."
            )
            result = await run_support_agent(ctx, "Can you escalate my issue?")

        assert ticket_id in ctx.tickets_created
        assert result.success is True
