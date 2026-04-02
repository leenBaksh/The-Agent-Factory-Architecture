# ══════════════════════════════════════════════════════════════════════════════
# Unit tests — Input guardrails
# Tests PII detection/masking, escalation keyword detection, sentiment scoring,
# and the three InputGuardrail functions.
# ══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


# ════════════════════════════════════════════════════════════════════════════
# detect_pii / mask_pii
# ════════════════════════════════════════════════════════════════════════════

class TestDetectPII:

    def test_detects_email(self):
        from app.agents.guardrails import detect_pii
        result = detect_pii("Contact me at user@example.com for details.")
        assert "email" in result
        assert "user@example.com" in result["email"]

    def test_detects_phone_us(self):
        from app.agents.guardrails import detect_pii
        result = detect_pii("Call me at 555-867-5309 anytime.")
        assert "phone" in result
        assert len(result["phone"]) > 0

    def test_detects_phone_e164(self):
        from app.agents.guardrails import detect_pii
        result = detect_pii("My number is +1 (800) 555-0100.")
        assert "phone" in result

    def test_detects_no_pii(self):
        from app.agents.guardrails import detect_pii
        result = detect_pii("My order is still processing.")
        # All lists should be empty when no PII is present
        assert all(len(v) == 0 for v in result.values())

    def test_detects_multiple_emails(self):
        from app.agents.guardrails import detect_pii
        result = detect_pii("Reply to alice@a.com or bob@b.com.")
        assert len(result["email"]) == 2

    def test_detects_mixed_pii(self):
        from app.agents.guardrails import detect_pii
        result = detect_pii("Email bob@example.com, call +15550001111.")
        assert len(result.get("email", [])) >= 1
        assert len(result.get("phone", [])) >= 1


class TestMaskPII:

    def test_masks_email(self):
        from app.agents.guardrails import mask_pii
        masked = mask_pii("Send invoice to bob@example.com please.")
        assert "bob@example.com" not in masked

    def test_masks_phone(self):
        from app.agents.guardrails import mask_pii
        masked = mask_pii("Call 555-867-5309 after 5pm.")
        assert "555-867-5309" not in masked

    def test_clean_text_unchanged(self):
        from app.agents.guardrails import mask_pii
        original = "I need help with my order."
        assert mask_pii(original) == original

    def test_masking_preserves_surrounding_text(self):
        from app.agents.guardrails import mask_pii
        masked = mask_pii("Hi, user@example.com is my email address.")
        assert "Hi," in masked
        assert "is my email address." in masked


# ════════════════════════════════════════════════════════════════════════════
# find_escalation_keyword
# ════════════════════════════════════════════════════════════════════════════

class TestEscalationKeyword:

    @pytest.mark.parametrize("text,expected_hit", [
        ("I want a refund immediately",            "refund"),
        ("I will sue your company",                "sue"),
        ("This is fraud, you stole my money",      "fraud"),
        ("I'll contact my lawyer about this",      "lawyer"),
        ("This is a GDPR violation",               "gdpr"),
        ("I'll file a chargeback with my bank",    "chargeback"),
        ("I'm filing a legal complaint",           "legal"),
        ("Please help me with my order",           None),
        ("The product arrived damaged",            None),
    ])
    def test_keyword_detection(self, text, expected_hit):
        from app.agents.guardrails import find_escalation_keyword
        result = find_escalation_keyword(text)
        if expected_hit is None:
            assert result is None
        else:
            assert result is not None
            assert expected_hit in result.lower()

    def test_case_insensitive(self):
        from app.agents.guardrails import find_escalation_keyword
        assert find_escalation_keyword("I WANT A REFUND") is not None

    def test_partial_word_not_matched(self):
        from app.agents.guardrails import find_escalation_keyword
        # "suing" contains "sue" — should still trigger
        assert find_escalation_keyword("I am suing your company") is not None


# ════════════════════════════════════════════════════════════════════════════
# sentiment_score
# ════════════════════════════════════════════════════════════════════════════

class TestSentimentScore:

    def test_very_negative_scores_high(self):
        from app.agents.guardrails import sentiment_score
        score = sentiment_score(
            "I am absolutely furious! This is the worst service I have EVER experienced!"
        )
        assert score > 0.5, f"Expected >0.5, got {score}"

    def test_neutral_text_scores_low(self):
        from app.agents.guardrails import sentiment_score
        score = sentiment_score("My order is number 12345.")
        assert score < 0.4, f"Expected <0.4, got {score}"

    def test_positive_text_scores_low(self):
        from app.agents.guardrails import sentiment_score
        score = sentiment_score("Thank you so much! The product is wonderful.")
        assert score < 0.3, f"Expected <0.3, got {score}"

    def test_returns_float_between_0_and_1(self):
        from app.agents.guardrails import sentiment_score
        score = sentiment_score("Something happened.")
        assert 0.0 <= score <= 1.0


# ════════════════════════════════════════════════════════════════════════════
# Guardrail functions
# ════════════════════════════════════════════════════════════════════════════

def _make_ctx(agent_context):
    """Wrap AgentContext in a minimal RunContextWrapper-like object."""
    ctx = MagicMock()
    ctx.context = agent_context
    return ctx


class TestPIIGuardrail:

    @pytest.mark.asyncio
    async def test_trips_on_pii(self, agent_context):
        from app.agents.guardrails import _pii_guardrail_fn
        ctx = _make_ctx(agent_context)
        agent = MagicMock()

        output = await _pii_guardrail_fn(ctx, agent, "My email is user@example.com")

        assert output.tripwire_triggered is True

    @pytest.mark.asyncio
    async def test_passes_clean_input(self, agent_context):
        from app.agents.guardrails import _pii_guardrail_fn
        ctx = _make_ctx(agent_context)
        agent = MagicMock()

        output = await _pii_guardrail_fn(ctx, agent, "I need help with my order status.")

        assert output.tripwire_triggered is False

    @pytest.mark.asyncio
    async def test_output_contains_masked_content(self, agent_context):
        from app.agents.guardrails import _pii_guardrail_fn
        ctx = _make_ctx(agent_context)
        agent = MagicMock()

        output = await _pii_guardrail_fn(ctx, agent, "Contact me at secret@email.com")

        # Even when tripped, output text should not contain the raw PII
        if output.output_info:
            assert "secret@email.com" not in str(output.output_info)


class TestKeywordEscalationGuardrail:

    @pytest.mark.asyncio
    async def test_trips_on_legal_keyword(self, agent_context):
        from app.agents.guardrails import _keyword_escalation_fn
        ctx = _make_ctx(agent_context)
        agent = MagicMock()

        output = await _keyword_escalation_fn(
            ctx, agent, "I am going to sue your company for damages."
        )

        assert output.tripwire_triggered is True

    @pytest.mark.asyncio
    async def test_trips_on_fraud_keyword(self, agent_context):
        from app.agents.guardrails import _keyword_escalation_fn
        ctx = _make_ctx(agent_context)
        agent = MagicMock()

        output = await _keyword_escalation_fn(
            ctx, agent, "This is fraud! You charged me twice!"
        )

        assert output.tripwire_triggered is True

    @pytest.mark.asyncio
    async def test_passes_normal_complaint(self, agent_context):
        from app.agents.guardrails import _keyword_escalation_fn
        ctx = _make_ctx(agent_context)
        agent = MagicMock()

        output = await _keyword_escalation_fn(
            ctx, agent, "My package arrived damaged, please help."
        )

        assert output.tripwire_triggered is False


class TestSentimentGuardrail:

    @pytest.mark.asyncio
    async def test_trips_on_extreme_negativity(self, agent_context):
        from app.agents.guardrails import _sentiment_guardrail_fn
        ctx = _make_ctx(agent_context)
        agent = MagicMock()

        output = await _sentiment_guardrail_fn(
            ctx,
            agent,
            "I am ABSOLUTELY OUTRAGED! This is the most disgusting, pathetic, "
            "horrible service I have ever encountered in my entire life! UNACCEPTABLE!!!",
        )

        assert output.tripwire_triggered is True

    @pytest.mark.asyncio
    async def test_passes_mild_frustration(self, agent_context):
        from app.agents.guardrails import _sentiment_guardrail_fn
        ctx = _make_ctx(agent_context)
        agent = MagicMock()

        output = await _sentiment_guardrail_fn(
            ctx, agent, "I'm a bit disappointed the delivery took so long."
        )

        # Mild frustration should not cross the 0.60 threshold
        assert output.tripwire_triggered is False

    @pytest.mark.asyncio
    async def test_passes_neutral_inquiry(self, agent_context):
        from app.agents.guardrails import _sentiment_guardrail_fn
        ctx = _make_ctx(agent_context)
        agent = MagicMock()

        output = await _sentiment_guardrail_fn(
            ctx, agent, "What is the status of order #54321?"
        )

        assert output.tripwire_triggered is False


# ════════════════════════════════════════════════════════════════════════════
# Guardrail instances are exported
# ════════════════════════════════════════════════════════════════════════════

class TestGuardrailExports:

    def test_pii_guardrail_is_input_guardrail(self):
        from agents import InputGuardrail
        from app.agents.guardrails import pii_guardrail
        assert isinstance(pii_guardrail, InputGuardrail)

    def test_keyword_escalation_guardrail_is_input_guardrail(self):
        from agents import InputGuardrail
        from app.agents.guardrails import keyword_escalation_guardrail
        assert isinstance(keyword_escalation_guardrail, InputGuardrail)

    def test_sentiment_guardrail_is_input_guardrail(self):
        from agents import InputGuardrail
        from app.agents.guardrails import sentiment_guardrail
        assert isinstance(sentiment_guardrail, InputGuardrail)
