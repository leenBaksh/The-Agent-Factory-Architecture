"""
Integration module for Dapr Workflows in Customer Success FTE

This module integrates Dapr Workflows with the existing FastAPI application.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from .workflows.dapr_workflows import (
    WorkflowInput,
    start_workflow_runtime,
    stop_workflow_runtime,
    get_workflow_runner,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan_with_dapr(app: FastAPI) -> AsyncGenerator:
    """
    Lifespan context manager that includes Dapr workflow runtime.

    Use this in your FastAPI app to automatically start/stop Dapr workflows.
    """
    # Startup
    logger.info("Starting Dapr workflow runtime...")
    try:
        runner = start_workflow_runtime()
        logger.info("Dapr workflow runtime started successfully")
    except Exception as e:
        logger.warning(f"Failed to start Dapr workflow runtime: {e}")
        logger.info("Continuing without Dapr workflows...")
        runner = None

    yield

    # Shutdown
    if runner:
        logger.info("Stopping Dapr workflow runtime...")
        stop_workflow_runtime()
        logger.info("Dapr workflow runtime stopped")


async def start_support_workflow(
    message_id: str,
    customer_id: str,
    channel: str,
    content: str,
    conversation_id: str | None = None,
    ticket_id: str | None = None,
) -> str:
    """
    Start a customer support workflow.

    Args:
        message_id: Unique message identifier
        customer_id: Customer identifier
        channel: Communication channel (web, gmail, whatsapp)
        content: Message content
        conversation_id: Optional conversation ID
        ticket_id: Optional existing ticket ID

    Returns:
        Workflow instance ID
    """
    workflow_input = WorkflowInput(
        message_id=message_id,
        customer_id=customer_id,
        channel=channel,
        content=content,
        conversation_id=conversation_id,
        ticket_id=ticket_id,
    )

    runner = get_workflow_runner()
    if runner.runtime is None:
        raise RuntimeError("Dapr workflow runtime not running")

    instance_id = await runner.start_workflow(workflow_input)
    logger.info(f"Started support workflow {instance_id}")

    return instance_id
