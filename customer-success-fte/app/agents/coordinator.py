"""
OpenAI Agents SDK coordinator.

Defines the support_agent (Agent instance) and run_support_agent(),
which is the single entry point called by the Kafka worker for every
inbound customer message.

Flow per message:
  1. Pre-process: mask PII in the raw content.
  2. Run the agent — guardrails execute before any LLM call.
  3. If a guardrail trips → auto-escalate without invoking the LLM.
  4. Capture AgentMetric for observability (tokens, latency, escalation).
  5. Return AgentResult to the caller.
"""

import logging
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from agents import Agent, Runner
from agents.exceptions import InputGuardrailTripwireTriggered

from app.agents.guardrails import (
    keyword_escalation_guardrail,
    mask_pii,
    pii_guardrail,
    sentiment_guardrail,
)
from app.agents.tools import (
    AgentContext,
    create_ticket,
    escalate_to_human,
    get_customer_history,
    resolve_ticket,
    search_knowledge_base,
    send_response,
)
from app.agents.claude_agent import (
    get_hybrid_orchestrator,
    HybridOrchestrator,
    ANTHROPIC_AVAILABLE,
)
from app.config import get_settings
from app.database import (
    ChannelType,
    MessageDirection,
    MessageStatus,
    TicketPriority,
    TicketStatus,
)
from app.repositories.agent_metrics import AgentMetricRepository
from app.repositories.messages import MessageRepository
from app.repositories.tickets import TicketRepository
from app.services.kafka_producer import kafka_producer
from app.services.metrics_service import log_agent_action

logger = logging.getLogger(__name__)
settings = get_settings()


# ── System instructions ────────────────────────────────────────────────────────

_SYSTEM_INSTRUCTIONS = """\
You are a professional customer support agent for a software company.
Your mission is to resolve customer issues efficiently, accurately, and empathetically.

## Core behaviour
- Be professional, warm, and concise. Never be dismissive or condescending.
- Read the full message carefully before deciding on an action.
- If the issue is ambiguous, ask ONE focused clarifying question.
- Always search the knowledge base before formulating a reply.
- Review customer history to personalise your response.

## Standard workflow for every message
1. Call `search_knowledge_base` with the customer's issue as the query.
2. Call `get_customer_history` to understand prior context.
3. If the issue requires tracking, call `create_ticket` with the correct priority.
4. Compose a clear, actionable response and call `send_response`.
5. If you cannot resolve the issue after checking the knowledge base and history,
   call `escalate_to_human` with a detailed reason, then call `send_response`
   to acknowledge the escalation to the customer.

## When the issue is fully resolved
- Call `resolve_ticket` BEFORE `send_response` with a concise resolution summary.
- This closes the ticket and automatically sends the customer a satisfaction survey.
- Only call resolve_ticket when you are certain the issue is fully addressed — not
  for partial answers or when further customer input is required.

## Priority guidelines
| Priority | Criteria |
|----------|----------|
| Critical | Service down, data loss, security breach, all users affected |
| High     | Core feature broken, no workaround, multiple users affected |
| Medium   | Partial degradation, workaround exists, single team affected |
| Low      | How-to question, cosmetic issue, feature request |

## Tone and format
- Keep replies under 200 words unless step-by-step guidance is required.
- Use numbered lists for multi-step guidance.
- Never share internal ticket IDs, raw error logs, or system internals.
- Close every reply with an offer to help further.

## When to escalate immediately
- The customer is highly frustrated and the issue cannot be resolved from the KB.
- The issue involves billing disputes, refund requests, or contract questions.
- Security incidents or data privacy concerns are reported.
- When escalating: call `escalate_to_human` FIRST, then `send_response` to inform
  the customer that a human specialist will follow up shortly.

## Hybrid orchestration - when to delegate to Claude
For complex tasks requiring advanced capabilities, set delegate_to_claude=True with:
- task_type: One of ["computer_use", "bash", "complex_reasoning", "mcp_interaction", "gui_automation"]
- task_description: Clear description of what Claude should do
This enables hybrid execution using both OpenAI (orchestration) and Claude (specialized tasks).
"""


# ── Agent definition ───────────────────────────────────────────────────────────

support_agent: Agent[AgentContext] = Agent(
    name="Customer Support Agent",
    model=settings.openai_model,
    instructions=_SYSTEM_INSTRUCTIONS,
    tools=[
        create_ticket,
        search_knowledge_base,
        get_customer_history,
        escalate_to_human,
        resolve_ticket,
        send_response,
    ],
    input_guardrails=[
        pii_guardrail,                   # log PII — non-blocking
        keyword_escalation_guardrail,    # legal/financial keywords — blocks
        sentiment_guardrail,             # high anger score — blocks
    ],
)


# ── Result dataclass ───────────────────────────────────────────────────────────

@dataclass
class AgentResult:
    """Outcome returned to the Kafka worker after one agent run."""

    success:           bool
    message_id:        uuid.UUID
    final_output:      Optional[str] = None
    escalated:         bool = False
    escalation_reason: Optional[str] = None
    latency_ms:        int = 0
    error:             Optional[str] = None
    # Hybrid orchestration fields
    delegated_to_claude: bool = False
    claude_task_type: Optional[str] = None
    claude_result: Optional[dict] = None


# ── Auto-escalation response templates ────────────────────────────────────────

_KEYWORD_ESCALATION_RESPONSE = (
    "Thank you for reaching out. I've flagged your message for immediate review "
    "by one of our senior support specialists, who will follow up with you shortly. "
    "We take these matters seriously and want to ensure you receive the right support."
)

_SENTIMENT_ESCALATION_RESPONSE = (
    "I'm genuinely sorry to hear you're having such a frustrating experience — "
    "that is not the level of service we aim to provide. I've escalated your case "
    "to a senior support agent who will personally follow up with you as soon as "
    "possible. Thank you for your patience."
)


# ── Guardrail auto-escalation ─────────────────────────────────────────────────

async def _handle_guardrail_escalation(
    exc: InputGuardrailTripwireTriggered,
    context: AgentContext,
    auto_response: str,
    escalation_reason: str,
) -> None:
    """
    When a guardrail trips, bypass the agent and:
      1. Create a high-priority ticket with escalated status.
      2. Publish a Kafka escalation event.
      3. Save an outbound auto-response message to the DB.
    """
    ticket_repo = TicketRepository(context.session)
    msg_repo = MessageRepository(context.session)

    # Create and immediately escalate a ticket
    ticket = await ticket_repo.create(
        conversation_id=context.conversation_id,
        customer_id=context.customer_id,
        subject="Auto-escalated by guardrail",
        priority=TicketPriority.high,
        status=TicketStatus.escalated,
        assigned_to="human",
        escalated_at=datetime.now(timezone.utc),
        tags=[],
        metadata_={
            "escalation_reason": escalation_reason,
            "auto_escalated": True,
            "guardrail": True,
        },
    )

    await kafka_producer.publish_escalation(
        ticket_id=ticket.id,
        conversation_id=context.conversation_id,
        customer_id=context.customer_id,
        reason=escalation_reason,
    )

    # Save the outbound auto-response
    now = datetime.now(timezone.utc)
    await msg_repo.create(
        conversation_id=context.conversation_id,
        customer_id=context.customer_id,
        direction=MessageDirection.outbound,
        channel=ChannelType(context.channel),
        status=MessageStatus.replied,
        content=auto_response,
        raw_payload={},
        agent_response=auto_response,
        replied_at=now,
    )

    # Mark inbound message as replied
    inbound = await msg_repo.get(context.message_id)
    if inbound:
        await msg_repo.update(
            inbound,
            status=MessageStatus.replied,
            agent_response=auto_response,
            replied_at=now,
        )

    logger.info(
        "Guardrail auto-escalation complete: ticket_id=%s reason=%r",
        ticket.id,
        escalation_reason,
    )


# ── Main entry point ───────────────────────────────────────────────────────────

async def run_support_agent(
    context: AgentContext,
    content: str,
) -> AgentResult:
    """
    Process one inbound customer message through the support agent.

    Called by the Kafka worker (Step 6) for every message on the inbound topic.

    Args:
        context: AgentContext holding the DB session and message identifiers.
        content: Raw customer message text (PII is masked before the LLM sees it).

    Returns:
        AgentResult describing the outcome (success, escalation, error, latency).
    """
    start_ms = time.monotonic()

    # ── 1. Mask PII before passing to the LLM ────────────────────────────────
    safe_content = mask_pii(content)
    logger.info(
        "Starting agent run: message_id=%s channel=%s",
        context.message_id,
        context.channel,
    )

    # ── 2. Run the agent ──────────────────────────────────────────────────────
    try:
        result = await Runner.run(
            support_agent,
            input=safe_content,
            context=context,
        )

        # ── 2b. Hybrid orchestration - delegate to Claude if needed ───────────
        claude_result = None
        delegated_to_claude = False
        claude_task_type = None
        
        if ANTHROPIC_AVAILABLE:
            # Check if the agent response indicates Claude delegation
            # This would be set by the agent in its output or metadata
            agent_metadata = getattr(result, 'metadata', {}) or {}
            delegate_to_claude = agent_metadata.get('delegate_to_claude', False)
            
            if delegate_to_claude:
                claude_task_type = agent_metadata.get('task_type', 'general')
                task_description = agent_metadata.get('task_description', safe_content)
                
                logger.info(
                    "Delegating to Claude: message_id=%s task_type=%s",
                    context.message_id,
                    claude_task_type,
                )
                
                # Get hybrid orchestrator and delegate
                orchestrator = get_hybrid_orchestrator()
                claude_result = await orchestrator.delegate_to_claude(
                    task=task_description,
                    task_type=claude_task_type,
                    context={
                        "customer_message": content,
                        "message_id": str(context.message_id),
                        "conversation_id": str(context.conversation_id),
                    }
                )
                
                delegated_to_claude = True
                logger.info(
                    "Claude delegation complete: message_id=%s success=%s",
                    context.message_id,
                    claude_result.get('success', False),
                )

        latency_ms = int((time.monotonic() - start_ms) * 1000)
        logger.info(
            "Agent run complete: message_id=%s latency_ms=%d delegated=%s",
            context.message_id,
            latency_ms,
            delegated_to_claude,
        )

        # ── 3. Record metrics ────────────────────────────────────────────────
        await _record_metrics(
            context=context,
            result=result,
            latency_ms=latency_ms,
            escalated=False,
        )

        log_agent_action(
            "agent_run_complete",
            message_id=str(context.message_id),
            conversation_id=str(context.conversation_id),
            channel=context.channel,
            latency_ms=latency_ms,
            escalated=False,
            tools_called=len(getattr(result, "new_items", [])),
        )

        return AgentResult(
            success=True,
            message_id=context.message_id,
            final_output=result.final_output,
            latency_ms=latency_ms,
            delegated_to_claude=delegated_to_claude,
            claude_task_type=claude_task_type,
            claude_result=claude_result,
        )

    # ── 4. Guardrail tripwire → auto-escalate ─────────────────────────────────
    except InputGuardrailTripwireTriggered as exc:
        latency_ms = int((time.monotonic() - start_ms) * 1000)

        # Safely extract guardrail output_info (SDK version-agnostic)
        output_info: dict = {}
        try:
            output_info = exc.guardrail_result.output.output_info or {}
        except AttributeError:
            pass

        reason_code: str = output_info.get("reason", "guardrail_tripwire")
        keyword: str | None = output_info.get("keyword")
        score: float | None = output_info.get("score")

        if reason_code == "keyword_escalation":
            escalation_reason = (
                f"Auto-escalated: message contains sensitive keyword '{keyword}'"
            )
            auto_response = _KEYWORD_ESCALATION_RESPONSE
        else:
            escalation_reason = (
                f"Auto-escalated: high anger sentiment score {score:.2f}"
                if score is not None
                else "Auto-escalated: negative sentiment detected"
            )
            auto_response = _SENTIMENT_ESCALATION_RESPONSE

        logger.info(
            "Guardrail tripped: message_id=%s reason=%r",
            context.message_id,
            escalation_reason,
        )

        await _handle_guardrail_escalation(
            exc=exc,
            context=context,
            auto_response=auto_response,
            escalation_reason=escalation_reason,
        )

        log_agent_action(
            "guardrail_escalation",
            message_id=str(context.message_id),
            conversation_id=str(context.conversation_id),
            channel=context.channel,
            reason=escalation_reason,
            latency_ms=latency_ms,
        )

        return AgentResult(
            success=True,
            message_id=context.message_id,
            final_output=auto_response,
            escalated=True,
            escalation_reason=escalation_reason,
            latency_ms=latency_ms,
        )

    # ── 5. Unexpected failure ─────────────────────────────────────────────────
    except Exception as exc:
        latency_ms = int((time.monotonic() - start_ms) * 1000)
        logger.exception(
            "Agent run failed: message_id=%s latency_ms=%d error=%s",
            context.message_id,
            latency_ms,
            exc,
        )
        log_agent_action(
            "agent_run_failed",
            message_id=str(context.message_id),
            conversation_id=str(context.conversation_id),
            channel=context.channel,
            latency_ms=latency_ms,
            error=str(exc),
        )
        return AgentResult(
            success=False,
            message_id=context.message_id,
            latency_ms=latency_ms,
            error=str(exc),
        )


# ── Observability helper ───────────────────────────────────────────────────────

async def _record_metrics(
    context: AgentContext,
    result,
    latency_ms: int,
    escalated: bool,
) -> None:
    """Persist an AgentMetric row for cost tracking and eval regressions."""
    try:
        # Extract token usage from the run result
        usage = getattr(result, "usage", None)
        prompt_tokens     = getattr(usage, "input_tokens", 0) if usage else 0
        completion_tokens = getattr(usage, "output_tokens", 0) if usage else 0
        total_tokens      = prompt_tokens + completion_tokens

        # Collect tool names called during the run
        tools_called: list[str] = []
        try:
            for item in getattr(result, "new_items", []):
                if hasattr(item, "type") and item.type == "tool_call_item":
                    tools_called.append(getattr(item, "name", "unknown"))
        except Exception:
            pass

        repo = AgentMetricRepository(context.session)
        ticket_id = context.tickets_created[-1] if context.tickets_created else None

        await repo.create(
            message_id=context.message_id,
            ticket_id=ticket_id,
            model=settings.openai_model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            tools_called=tools_called,
            was_escalated=escalated,
            metadata_={"channel": context.channel},
        )
        logger.debug(
            "Metrics recorded: message_id=%s tokens=%d latency_ms=%d",
            context.message_id,
            total_tokens,
            latency_ms,
        )
    except Exception as exc:
        # Metrics failure must never break the main flow
        logger.warning(
            "Failed to record agent metrics: message_id=%s error=%s",
            context.message_id,
            exc,
        )
