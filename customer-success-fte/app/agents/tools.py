"""
OpenAI Agents SDK function tools.

All tools receive a RunContextWrapper[AgentContext] as their first argument.
The SDK injects this automatically — do not pass it manually.

Tools defined here:
  • create_ticket          — create a support ticket in PostgreSQL
  • search_knowledge_base  — semantic search via pgvector + OpenAI embeddings
  • get_customer_history   — fetch recent conversations for context
  • escalate_to_human      — update ticket status + publish Kafka escalation event
  • send_response          — persist outbound message + deliver via channel API
  • resolve_ticket         — mark ticket resolved + send satisfaction survey
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import httpx
from agents import RunContextWrapper, function_tool
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import (
    ChannelType,
    MessageDirection,
    MessageStatus,
    TicketPriority,
    TicketStatus,
)
from app.repositories.conversations import ConversationRepository
from app.repositories.knowledge_base import KnowledgeBaseRepository
from app.repositories.messages import MessageRepository
from app.repositories.tickets import TicketRepository
from app.services.kafka_producer import kafka_producer

logger = logging.getLogger(__name__)
settings = get_settings()

_openai = AsyncOpenAI(api_key=settings.openai_api_key)


# ── Agent context ──────────────────────────────────────────────────────────────


@dataclass
class AgentContext:
    """
    Runtime context injected into every tool call via RunContextWrapper.

    Created by the Kafka worker once per inbound message and passed to
    Runner.run(agent, input=..., context=agent_context).
    """

    session:         AsyncSession
    message_id:      uuid.UUID
    conversation_id: uuid.UUID
    customer_id:     uuid.UUID
    channel:         str                   # "web" | "gmail" | "whatsapp"
    customer_email:            Optional[str] = None
    customer_phone:            Optional[str] = None
    tickets_created:           list[uuid.UUID] = field(default_factory=list)
    outbound_messages_created: list[uuid.UUID] = field(default_factory=list)


# ── Internal helpers ───────────────────────────────────────────────────────────


async def _get_embedding(text: str) -> list[float]:
    """Generate a text embedding via the configured OpenAI embedding model."""
    response = await _openai.embeddings.create(
        model=settings.openai_embedding_model,
        input=text[:8_000],        # stay within token limits
    )
    return response.data[0].embedding


async def _send_whatsapp(phone: str, text: str) -> None:
    """
    POST a text message to a recipient phone number via the Meta Cloud API.
    Raises httpx.HTTPStatusError on non-2xx responses.
    """
    url = (
        f"{settings.whatsapp_api_url}"
        f"/{settings.whatsapp_phone_number_id}/messages"
    )
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            url,
            json={
                "messaging_product": "whatsapp",
                "to": phone,
                "type": "text",
                "text": {"body": text},
            },
            headers={"Authorization": f"Bearer {settings.whatsapp_access_token}"},
        )
        resp.raise_for_status()
    logger.info("WhatsApp message delivered to %s.", phone)


# ── Tools ──────────────────────────────────────────────────────────────────────


@function_tool
async def create_ticket(
    context: RunContextWrapper[AgentContext],
    subject: str,
    priority: str,
    category: str = "",
    description: str = "",
) -> str:
    """
    Create a support ticket for the current customer and link it to the
    active conversation. Returns a confirmation string with the ticket ID.

    Args:
        subject:     One-line summary of the issue (max 512 chars).
        priority:    Severity — one of: low, medium, high, critical.
        category:    Issue type — e.g. Bug, Billing, How-to, Account,
                     Integration, Performance, Security, Data, Feature request.
        description: Optional detailed description or steps to reproduce.
    """
    ctx = context.context

    try:
        ticket_priority = TicketPriority(priority.lower())
    except ValueError:
        logger.warning("Unknown priority %r — defaulting to medium.", priority)
        ticket_priority = TicketPriority.medium

    repo = TicketRepository(ctx.session)
    ticket = await repo.create(
        conversation_id=ctx.conversation_id,
        customer_id=ctx.customer_id,
        subject=subject,
        priority=ticket_priority,
        category=category or None,
        description=description or None,
        tags=[],
        metadata_={},
    )

    ctx.tickets_created.append(ticket.id)
    logger.info(
        "Ticket created: id=%s subject=%r priority=%s customer=%s",
        ticket.id,
        subject,
        prio.value,
        ctx.customer_id,
    )
    return (
        f"Ticket created successfully.\n"
        f"  ID: {ticket.id}\n"
        f"  Priority: {prio.value}\n"
        f"  Category: {category or 'Unset'}"
    )


@function_tool
async def search_knowledge_base(
    context: RunContextWrapper[AgentContext],
    query: str,
    limit: int = 5,
) -> str:
    """
    Search the knowledge base for articles relevant to the customer's issue
    using semantic similarity (pgvector cosine search). Returns the top matches
    with title, category, and a content snippet.

    Args:
        query: Natural-language description of the issue or question.
        limit: Maximum results to return (1–10, default 5).
    """
    limit = max(1, min(limit, 10))

    logger.debug("Knowledge base search: query=%r limit=%d", query, limit)

    try:
        embedding = await _get_embedding(query)
    except Exception as exc:
        logger.error("Embedding generation failed: %s", exc)
        return "Knowledge base search unavailable — embedding service error."

    repo = KnowledgeBaseRepository(context.context.session)
    results = await repo.semantic_search(embedding, limit=limit, min_score=0.60)

    if not results:
        return (
            "No knowledge base articles matched this query. "
            "If the issue is unclear, ask the customer for more detail. "
            "If you cannot resolve it, escalate to a human agent."
        )

    lines = [f"Found {len(results)} relevant knowledge base article(s):\n"]
    for i, article in enumerate(results, 1):
        snippet = article.content[:400].replace("\n", " ")
        ellipsis = "…" if len(article.content) > 400 else ""
        lines.append(
            f"{i}. [{article.category or 'General'}] **{article.title}**\n"
            f"   {snippet}{ellipsis}"
        )

    return "\n\n".join(lines)


@function_tool
async def get_customer_history(
    context: RunContextWrapper[AgentContext],
    max_conversations: int = 5,
) -> str:
    """
    Retrieve recent conversation history for the current customer. Use this
    to personalise your response, identify recurring issues, and avoid asking
    for information the customer has already provided.

    Args:
        max_conversations: Number of past conversations to fetch (1–10, default 5).
    """
    ctx = context.context
    max_conversations = max(1, min(max_conversations, 10))

    conv_repo    = ConversationRepository(ctx.session)
    msg_repo     = MessageRepository(ctx.session)
    ticket_repo  = TicketRepository(ctx.session)

    conversations = await conv_repo.list_by_customer(
        ctx.customer_id, limit=max_conversations
    )

    if not conversations:
        return "No prior conversations found for this customer — this appears to be their first contact."

    lines = [f"Customer history: {len(conversations)} conversation(s) found.\n"]

    for conv in conversations:
        messages = await msg_repo.list_by_conversation(conv.id, limit=6)
        tickets  = await ticket_repo.list_by_conversation(conv.id)

        ticket_info = ""
        if tickets:
            ticket_info = " | Tickets: " + ", ".join(
                f"{t.status.value}/{t.priority.value}"
                for t in tickets
            )

        lines.append(
            f"── [{conv.channel.value.upper()}] {conv.started_at.strftime('%Y-%m-%d')} "
            f"| Status: {conv.status.value}{ticket_info}"
        )

        for msg in messages:
            direction_label = "Customer" if msg.direction.value == "inbound" else "Agent"
            snippet = msg.content[:150].replace("\n", " ")
            ellipsis = "…" if len(msg.content) > 150 else ""
            lines.append(f"  {direction_label}: {snippet}{ellipsis}")

    logger.debug(
        "Customer history fetched: customer_id=%s conversations=%d",
        ctx.customer_id,
        len(conversations),
    )
    return "\n".join(lines)


@function_tool
async def escalate_to_human(
    context: RunContextWrapper[AgentContext],
    reason: str,
    ticket_id: str = "",
) -> str:
    """
    Escalate the issue to a human support agent. Updates the ticket status
    to 'escalated', sets the escalation timestamp, and publishes a Kafka event
    so the human team is notified immediately.

    Call this BEFORE send_response when escalating, so the human agent has
    context before the customer receives the escalation acknowledgement.

    Args:
        reason:    Clear explanation of why this requires human attention.
                   Include what you tried and why it was insufficient.
        ticket_id: UUID of an existing ticket. If blank, the most recently
                   created ticket in this session is used. If none exists,
                   a new one is created automatically.
    """
    ctx = context.context
    repo = TicketRepository(ctx.session)

    # ── Resolve target ticket ──────────────────────────────────────────────────
    target_id: uuid.UUID | None = None

    if ticket_id:
        try:
            target_id = uuid.UUID(ticket_id)
        except ValueError:
            return f"Invalid ticket_id format: {ticket_id!r}. Provide a valid UUID."

    elif ctx.tickets_created:
        target_id = ctx.tickets_created[-1]

    # Create a stub ticket if nothing exists to escalate
    if target_id is None:
        ticket = await repo.create(
            conversation_id=ctx.conversation_id,
            customer_id=ctx.customer_id,
            subject="Escalated — no prior ticket",
            priority=TicketPriority.high,
            tags=[],
            metadata_={"auto_created_for_escalation": True},
        )
        target_id = ticket.id
        ctx.tickets_created.append(target_id)
        logger.info("Auto-created ticket %s for escalation.", target_id)

    # ── Update ticket status ───────────────────────────────────────────────────
    ticket = await repo.get_or_raise(target_id)
    await repo.update(
        ticket,
        status=TicketStatus.escalated,
        assigned_to="human",
        escalated_at=datetime.now(timezone.utc),
        metadata_={**ticket.metadata_, "escalation_reason": reason},
    )

    # ── Publish Kafka event ────────────────────────────────────────────────────
    await kafka_producer.publish_escalation(
        ticket_id=target_id,
        conversation_id=ctx.conversation_id,
        customer_id=ctx.customer_id,
        reason=reason,
    )

    logger.info(
        "Escalation published: ticket_id=%s customer_id=%s reason=%r",
        target_id,
        ctx.customer_id,
        reason,
    )
    return (
        f"Ticket {target_id} has been escalated to a human agent.\n"
        f"Reason logged: {reason}"
    )


@function_tool
async def send_response(
    context: RunContextWrapper[AgentContext],
    message: str,
) -> str:
    """
    Send a reply to the customer on their original channel and record it in
    the database. Handles Web, Gmail, and WhatsApp automatically based on
    the conversation channel.

    Call this as the FINAL step after any knowledge base lookups, ticket
    creation, or escalation calls.

    Args:
        message: The complete reply text to send to the customer.
                 Keep it professional, concise, and actionable.
    """
    ctx = context.context
    channel = ctx.channel
    now = datetime.now(timezone.utc)

    # ── 1. Persist outbound message ────────────────────────────────────────────
    msg_repo = MessageRepository(ctx.session)
    outbound = await msg_repo.create(
        conversation_id=ctx.conversation_id,
        customer_id=ctx.customer_id,
        direction=MessageDirection.outbound,
        channel=ChannelType(channel),
        status=MessageStatus.processing,  # Set to processing until delivery confirmed
        content=message,
        raw_payload={},
        agent_response=message,
        replied_at=now,
    )
    ctx.outbound_messages_created.append(outbound.id)
    logger.info(
        "Outbound message saved: id=%s channel=%s", outbound.id, channel
    )

    # ── 2. Mark inbound message as processing ─────────────────────────────────
    inbound = await msg_repo.get(ctx.message_id)
    if inbound:
        await msg_repo.update(
            inbound,
            status=MessageStatus.processing,
            agent_response=message,
        )

    # ── 3. Deliver via channel transport ──────────────────────────────────────
    delivery_status: str
    delivery_failed = False

    if channel == "whatsapp":
        if ctx.customer_phone:
            try:
                await _send_whatsapp(ctx.customer_phone, message)
                delivery_status = "delivered_whatsapp"
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "WhatsApp delivery failed for customer %s (HTTP %d): %s",
                    ctx.customer_id,
                    exc.response.status_code,
                    exc,
                )
                delivery_status = f"whatsapp_error_http_{exc.response.status_code}"
                delivery_failed = True
            except httpx.RequestError as exc:
                logger.error(
                    "WhatsApp delivery network error for customer %s: %s",
                    ctx.customer_id,
                    exc,
                )
                delivery_status = "whatsapp_error_network"
                delivery_failed = True
        else:
            logger.warning(
                "WhatsApp channel but customer_phone not in context — "
                "reply saved to DB only. customer_id=%s",
                ctx.customer_id,
            )
            delivery_status = "whatsapp_no_phone_in_context"
            delivery_failed = True

    elif channel == "gmail":
        # Outbound Gmail replies are picked up by the Gmail worker (Step 6),
        # which queries for outbound messages with status=replied and sends
        # them via the Gmail API in-thread.
        logger.info(
            "Gmail reply queued for worker delivery: outbound_id=%s", outbound.id
        )
        delivery_status = "queued_gmail_worker"

    elif channel == "web":
        # Web responses are served via GET /api/conversations/{id}/messages.
        # The Next.js frontend polls this endpoint (or subscribes via websocket).
        logger.info(
            "Web reply saved for frontend polling: outbound_id=%s", outbound.id
        )
        delivery_status = "saved_web_db"

    else:
        logger.warning("Unknown channel %r — reply saved to DB only.", channel)
        delivery_status = f"unknown_channel_{channel}"
        delivery_failed = True

    # ── 4. Update message status based on delivery result ─────────────────────
    final_status = MessageStatus.failed if delivery_failed else MessageStatus.replied
    await msg_repo.update(outbound, status=final_status)
    
    if inbound:
        await msg_repo.update(inbound, status=final_status, replied_at=now)
    
    if delivery_failed:
        logger.warning(
            "Message delivery failed: outbound_id=%s status=%s channel=%s",
            outbound.id,
            delivery_status,
            channel,
        )
    else:
        logger.info(
            "send_response complete: channel=%s status=%s outbound_id=%s",
            channel,
            delivery_status,
            outbound.id,
        )
    return f"Response delivered. Status: {delivery_status} | Message ID: {outbound.id}"


@function_tool
async def resolve_ticket(
    context: RunContextWrapper[AgentContext],
    resolution: str,
    ticket_id: str = "",
) -> str:
    """
    Mark a support ticket as resolved and send a satisfaction survey to the
    customer. Call this only after the issue is confirmed fully resolved.

    This should be called BEFORE send_response so the survey is dispatched
    while you compose the closing message to the customer.

    Args:
        resolution: One-to-three sentence summary of how the issue was resolved.
        ticket_id:  UUID of the ticket to resolve. If blank, the most recently
                    created ticket in this session is used.
    """
    ctx = context.context
    repo = TicketRepository(ctx.session)

    target_id: uuid.UUID | None = None

    if ticket_id:
        try:
            target_id = uuid.UUID(ticket_id)
        except ValueError:
            return f"Invalid ticket_id format: {ticket_id!r}. Provide a valid UUID."
    elif ctx.tickets_created:
        target_id = ctx.tickets_created[-1]

    if target_id is None:
        return (
            "No ticket found to resolve. "
            "Call create_ticket first, then resolve_ticket."
        )

    ticket = await repo.get_or_raise(target_id)

    from app.services.ticket_service import ticket_lifecycle_service

    await ticket_lifecycle_service.resolve_ticket(
        ticket=ticket,
        session=ctx.session,
        resolution=resolution,
        resolved_by="ai",
    )

    logger.info(
        "Ticket resolved via agent tool: ticket_id=%s resolution=%r",
        target_id,
        resolution[:80],
    )
    return (
        f"Ticket {target_id} marked as resolved.\n"
        f"Resolution: {resolution}\n"
        f"A satisfaction survey has been queued for the customer."
    )
