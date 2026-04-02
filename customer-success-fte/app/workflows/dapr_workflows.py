"""
Dapr Workflows for Customer Success FTE

This module implements durable workflows using Dapr Workflows SDK.
Workflows survive crashes, restarts, and scale events.

Note: Uses Dapr 1.15+ workflow API
"""

import asyncio
import logging
import uuid
import time
from datetime import timedelta
from typing import Any

import dapr.ext.workflow as wf
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Dapr workflow constants
WORKFLOW_NAME = "customer_support_workflow"


class WorkflowInput(BaseModel):
    """Input data for the customer support workflow"""

    message_id: str
    customer_id: str
    channel: str
    content: str
    conversation_id: str | None = None
    ticket_id: str | None = None


class WorkflowState(BaseModel):
    """State maintained throughout the workflow execution"""

    ticket_id: str | None = None
    conversation_id: str | None = None
    response_sent: bool = False
    survey_sent: bool = False
    escalated: bool = False
    resolution_time_minutes: float = 0
    first_response_time_minutes: float = 0
    sentiment_score: float = 0.5
    sla_status: str = "on_track"


# ============= Activity Functions =============

def send_response(ctx: wf.DaprWorkflowContext, input: dict) -> dict[str, Any]:
    """Send a response to the customer via the appropriate channel"""
    logger.info(f"Sending response to {input.get('channel')} for message {input.get('message_id')}")
    return {"status": "sent", "message_id": input.get("message_id")}


def create_ticket(ctx: wf.WorkflowActivityContext, input: dict) -> dict[str, Any]:
    """Create a new support ticket"""
    logger.info(f"Creating ticket for customer {input.get('customer_id')}")
    ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
    return {
        "ticket_id": ticket_id,
        "status": "open",
        "priority": input.get("priority", "medium"),
    }


def search_knowledge_base(ctx: wf.WorkflowActivityContext, query: str) -> list[dict[str, Any]]:
    """Search the knowledge base for relevant articles"""
    logger.info(f"Searching KB for: {query[:50]}...")
    return [
        {"id": "KB-001", "title": "Getting Started Guide", "relevance": 0.95},
        {"id": "KB-002", "title": "Troubleshooting Common Issues", "relevance": 0.87},
    ]


def escalate_to_human(ctx: wf.WorkflowActivityContext, input: dict) -> dict[str, Any]:
    """Escalate a ticket to human support"""
    logger.info(f"Escalating ticket {input.get('ticket_id')} to human")
    return {"ticket_id": input.get("ticket_id"), "escalated": True}


def send_survey(ctx: wf.WorkflowActivityContext, input: dict) -> dict[str, Any]:
    """Send a satisfaction survey to the customer"""
    logger.info(f"Sending survey for ticket {input.get('ticket_id')}")
    return {"status": "sent", "ticket_id": input.get("ticket_id")}


def update_ticket_status(ctx: wf.WorkflowActivityContext, input: dict) -> dict[str, Any]:
    """Update the status of a ticket"""
    logger.info(f"Updating ticket {input.get('ticket_id')} status to {input.get('status')}")
    return {"ticket_id": input.get("ticket_id"), "status": input.get("status")}


def check_sla_status(ctx: wf.WorkflowActivityContext, input: dict) -> dict[str, Any]:
    """Check if a ticket is at risk of SLA breach"""
    elapsed = input.get("elapsed_minutes", 0)
    sla_status = "on_track" if elapsed < 30 else "at_risk" if elapsed < 240 else "breached"
    return {"sla_status": sla_status, "elapsed_minutes": elapsed}


# ============= Workflow Definition =============

def customer_support_workflow(ctx: wf.DaprWorkflowContext, workflow_input: dict):
    """
    Main customer support workflow using Dapr Workflows.
    
    This workflow handles the entire customer support lifecycle:
    1. Create or update ticket
    2. Search knowledge base
    3. Generate and send response
    4. Monitor SLA compliance
    5. Send satisfaction survey
    """
    logger.info(f"Starting workflow for message {workflow_input.get('message_id')}")

    try:
        # Step 1: Create ticket if not exists
        ticket_id = workflow_input.get("ticket_id")
        if not ticket_id:
            ticket_input = {
                "customer_id": workflow_input.get("customer_id"),
                "content": workflow_input.get("content"),
                "channel": workflow_input.get("channel"),
                "priority": "medium",
            }
            ticket_result = ctx.call_activity(create_ticket, input=ticket_input)
            ticket_id = ticket_result["ticket_id"]
            logger.info(f"Created ticket {ticket_id}")

        # Step 2: Update ticket status to in_progress
        ctx.call_activity(update_ticket_status, input={"ticket_id": ticket_id, "status": "in_progress"})

        # Step 3: Search knowledge base
        kb_results = ctx.call_activity(search_knowledge_base, input=workflow_input.get("content", "")[:200])
        logger.info(f"Found {len(kb_results)} relevant KB articles")

        # Step 4: Generate and send response
        response_content = f"""Thank you for contacting support.

Based on your inquiry, here are some helpful resources:
- {kb_results[0]['title']}
- {kb_results[1]['title']}

Ticket ID: {ticket_id}
"""
        response_input = {
            "message_id": workflow_input.get("message_id"),
            "channel": workflow_input.get("channel"),
            "content": response_content,
        }
        ctx.call_activity(send_response, input=response_input)

        # Step 5: Update ticket status
        ctx.call_activity(update_ticket_status, input={"ticket_id": ticket_id, "status": "waiting_customer"})

        # Step 6: Wait for customer response (5 minutes for demo)
        ctx.create_timer(timedelta(minutes=5))

        # Step 7: Check SLA status
        ctx.call_activity(check_sla_status, input={"elapsed_minutes": 5})

        # Step 8: Mark as resolved
        ctx.call_activity(update_ticket_status, input={"ticket_id": ticket_id, "status": "resolved"})

        # Step 9: Wait before sending survey
        ctx.create_timer(timedelta(minutes=1))

        # Step 10: Send survey
        ctx.call_activity(send_survey, input={"ticket_id": ticket_id, "customer_id": workflow_input.get("customer_id")})

        # Step 11: Close ticket
        ctx.call_activity(update_ticket_status, input={"ticket_id": ticket_id, "status": "closed"})

        logger.info(f"Workflow completed successfully for ticket {ticket_id}")

        return {
            "ticket_id": ticket_id,
            "status": "completed",
            "survey_sent": True,
        }

    except Exception as e:
        logger.error(f"Workflow failed: {str(e)}")
        raise


# ============= Workflow Runner =============

class DaprWorkflowRunner:
    """Manages Dapr workflow runtime"""

    def __init__(self, host: str = "localhost", port: str = "50001"):
        self.host = host
        self.port = port
        self.runtime: wf.WorkflowRuntime | None = None

    def start(self):
        """Start the workflow runtime"""
        logger.info(f"Starting Dapr workflow runtime on {self.host}:{self.port}")

        self.runtime = wf.WorkflowRuntime(host=self.host, port=self.port)

        # Register workflow
        self.runtime.register_workflow(customer_support_workflow)

        # Register activities
        self.runtime.register_activity(send_response)
        self.runtime.register_activity(create_ticket)
        self.runtime.register_activity(search_knowledge_base)
        self.runtime.register_activity(escalate_to_human)
        self.runtime.register_activity(send_survey)
        self.runtime.register_activity(update_ticket_status)
        self.runtime.register_activity(check_sla_status)

        self.runtime.start()
        logger.info("Dapr workflow runtime started")

    def stop(self):
        """Stop the workflow runtime"""
        if self.runtime:
            logger.info("Stopping Dapr workflow runtime")
            self.runtime.shutdown()
            self.runtime = None


# Singleton instance
_workflow_runner: DaprWorkflowRunner | None = None


def get_workflow_runner() -> DaprWorkflowRunner:
    """Get or create the workflow runner singleton"""
    global _workflow_runner
    if _workflow_runner is None:
        _workflow_runner = DaprWorkflowRunner()
    return _workflow_runner


def start_workflow_runtime():
    """Start the global workflow runtime"""
    runner = get_workflow_runner()
    runner.start()
    return runner


def stop_workflow_runtime():
    """Stop the global workflow runtime"""
    runner = get_workflow_runner()
    runner.stop()
