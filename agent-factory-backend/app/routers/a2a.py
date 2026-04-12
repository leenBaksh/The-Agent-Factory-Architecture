"""
A2A Protocol - Agent-to-Agent Communication

Implements the A2A protocol for inter-FTE discovery and collaboration.
Based on JSON-RPC over HTTP with SSE for streaming updates.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Optional

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Agent Card Registry ───────────────────────────────────────────────────────

# Local registry of known FTEs
fte_registry: dict[str, dict[str, Any]] = {}


def register_fte_card(
    fte_id: str,
    name: str,
    description: str,
    url: str,
    version: str,
    capabilities: dict[str, Any],
    skills: list[dict[str, Any]],
    authentication: dict[str, Any],
):
    """Register an FTE's Agent Card."""
    fte_registry[fte_id] = {
        "name": name,
        "description": description,
        "url": url,
        "version": version,
        "capabilities": capabilities,
        "skills": skills,
        "authentication": authentication,
        "registered_at": datetime.now().isoformat(),
        "status": "active",
    }


# Register default FTEs
register_fte_card(
    fte_id="customer-success-1",
    name="Customer Success FTE",
    description="Automated customer support specialist with ticket management, SLA monitoring, and sentiment analysis",
    url="http://localhost:8001/a2a",
    version="1.0.0",
    capabilities={
        "streaming": True,
        "pushNotifications": False,
        "stateTransitionHistory": True,
        "ticketManagement": True,
        "slaMonitoring": True,
    },
    skills=[
        {
            "id": "customer-support",
            "description": "Ticket triage, response generation, escalation handling",
            "tags": ["support", "tickets", "customer"],
            "inputModes": ["text", "email", "chat"],
            "outputModes": ["text", "json", "artifacts"],
        },
        {
            "id": "sla-management",
            "description": "SLA compliance monitoring and breach prevention",
            "tags": ["sla", "compliance", "monitoring"],
            "inputModes": ["text"],
            "outputModes": ["json", "alerts"],
        },
    ],
    authentication={
        "type": "oauth2",
        "flows": ["client_credentials"],
    },
)

register_fte_card(
    fte_id="sales-support-1",
    name="Sales Support FTE",
    description="B2B sales development representative with lead qualification, ROI calculation, and proposal generation",
    url="http://localhost:8001/a2a",
    version="1.2.0",
    capabilities={
        "streaming": True,
        "pushNotifications": False,
        "stateTransitionHistory": True,
        "leadQualification": True,
        "roiCalculation": True,
    },
    skills=[
        {
            "id": "sales-methodology",
            "description": "MEDDIC, SPIN, Challenger Sale frameworks",
            "tags": ["sales", "qualification", "methodology"],
            "inputModes": ["text", "email"],
            "outputModes": ["text", "json", "proposals"],
        },
        {
            "id": "proposal-creation",
            "description": "Automated proposal generation with ROI calculations",
            "tags": ["proposals", "roi", "pricing"],
            "inputModes": ["text", "data"],
            "outputModes": ["documents", "json"],
        },
    ],
    authentication={
        "type": "oauth2",
        "flows": ["client_credentials"],
    },
)

register_fte_card(
    fte_id="technical-support-1",
    name="Technical Support FTE",
    description="Senior technical support engineer with debugging, log analysis, and infrastructure troubleshooting",
    url="http://localhost:8002/a2a",
    version="0.9.5",
    capabilities={
        "streaming": True,
        "pushNotifications": False,
        "stateTransitionHistory": True,
        "debugging": True,
        "logAnalysis": True,
    },
    skills=[
        {
            "id": "debugging-methodology",
            "description": "Systematic debugging, log analysis, isolation techniques",
            "tags": ["debugging", "technical", "troubleshooting"],
            "inputModes": ["text", "logs", "screenshots"],
            "outputModes": ["text", "json", "artifacts"],
        },
        {
            "id": "api-troubleshooting",
            "description": "API error diagnosis and resolution",
            "tags": ["api", "errors", "troubleshooting"],
            "inputModes": ["text", "json"],
            "outputModes": ["text", "json"],
        },
    ],
    authentication={
        "type": "oauth2",
        "flows": ["client_credentials"],
    },
)


# ── A2A Discovery Endpoint ────────────────────────────────────────────────────

@router.get("/.well-known/agent.json", tags=["A2A"])
async def get_agent_card():
    """
    A2A Agent Card for discovery by other Digital FTEs.
    
    This endpoint declares the Agent Factory's identity, capabilities,
    and available skills. Other agents query this to understand
    what tasks can be delegated to us.
    """
    return {
        "name": "Agent Factory Backend",
        "description": "Central orchestration service for Digital FTEs with metrics aggregation, FTE registry, and A2A coordination",
        "url": "http://localhost:8003/a2a",
        "version": "1.0.0",
        "capabilities": {
            "streaming": True,
            "pushNotifications": False,
            "stateTransitionHistory": True,
            "metricsAggregation": True,
            "fteRegistry": True,
        },
        "skills": [
            {
                "id": "metrics-aggregation",
                "description": "Aggregate and report on FTE performance metrics",
                "tags": ["metrics", "monitoring", "reporting"],
                "inputModes": ["text", "json"],
                "outputModes": ["json", "dashboards"],
            },
            {
                "id": "fte-coordination",
                "description": "Coordinate tasks across multiple Digital FTEs",
                "tags": ["coordination", "orchestration", "multi-agent"],
                "inputModes": ["text", "json"],
                "outputModes": ["json", "events"],
            },
        ],
        "authentication": {
            "type": "none",  # Open for discovery
        },
        "supportedModes": ["text", "json", "streaming"],
    }


@router.get("/ftes", tags=["A2A"])
async def list_known_ftes():
    """
    List all known FTEs with their Agent Cards.
    
    Returns the registry of FTEs that this Agent Factory knows about,
    enabling discovery and task delegation.
    """
    return {
        "ftes": [
            {
                "id": fte_id,
                **card,
            }
            for fte_id, card in fte_registry.items()
        ],
        "count": len(fte_registry),
    }


@router.get("/ftes/{fte_id}", tags=["A2A"])
async def get_fte_card(fte_id: str):
    """Get a specific FTE's Agent Card."""
    if fte_id not in fte_registry:
        raise HTTPException(status_code=404, detail=f"FTE '{fte_id}' not found")
    
    return {
        "id": fte_id,
        **fte_registry[fte_id],
    }


# ── A2A Task Delegation Endpoints ─────────────────────────────────────────────

# Active task tracking
a2a_tasks: dict[str, dict[str, Any]] = {}


@router.post("/tasks/send", tags=["A2A"])
async def delegate_task(request: dict):
    """
    A2A Protocol endpoint for receiving tasks from other FTEs.
    
    Implements JSON-RPC style interface for task delegation.
    Other FTEs call this to delegate work to this Agent Factory.
    
    Request format:
    {
        "jsonrpc": "2.0",
        "id": "request-uuid",
        "method": "tasks/send",
        "params": {
            "message": "Task description",
            "skill": "Requested skill ID (optional)",
            "from": "Requesting FTE ID",
            "context": { ... }  # Optional context
        }
    }
    """
    method = request.get("method")
    params = request.get("params", {})
    request_id = request.get("id")

    if method != "tasks/send":
        raise HTTPException(status_code=400, detail=f"Unknown method: {method}")

    # Extract task details
    task_message = params.get("message")
    skill_requested = params.get("skill")
    from_agent = params.get("from")
    context = params.get("context", {})

    if not task_message:
        raise HTTPException(status_code=400, detail="Task message is required")

    # Generate task ID
    task_id = str(uuid.uuid4())

    # Create task record
    task_record = {
        "task_id": task_id,
        "status": "accepted",
        "message": task_message,
        "skill_requested": skill_requested,
        "from_agent": from_agent,
        "context": context,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "updates": [],
    }

    # Store task
    a2a_tasks[task_id] = task_record

    logger.info(
        f"A2A task received from {from_agent}: {task_id}"
    )

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "task_id": task_id,
            "status": "accepted",
            "message": "Task accepted, processing will begin shortly",
        },
    }


@router.post("/tasks/status", tags=["A2A"])
async def get_task_status(request: dict):
    """
    Check status of a delegated task.
    
    Request format:
    {
        "jsonrpc": "2.0",
        "id": "request-uuid",
        "method": "tasks/status",
        "params": {
            "task_id": "task-uuid"
        }
    }
    """
    method = request.get("method")
    params = request.get("params", {})
    request_id = request.get("id")

    if method != "tasks/status":
        raise HTTPException(status_code=400, detail=f"Unknown method: {method}")

    task_id = params.get("task_id")
    if not task_id:
        raise HTTPException(status_code=400, detail="task_id is required")

    if task_id not in a2a_tasks:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    task = a2a_tasks[task_id]

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "task_id": task["task_id"],
            "status": task["status"],
            "updates": task["updates"],
            "created_at": task["created_at"],
            "updated_at": task["updated_at"],
        },
    }


@router.post("/tasks/cancel", tags=["A2A"])
async def cancel_task(request: dict):
    """
    Cancel a delegated task.
    
    Request format:
    {
        "jsonrpc": "2.0",
        "id": "request-uuid",
        "method": "tasks/cancel",
        "params": {
            "task_id": "task-uuid",
            "reason": "Cancellation reason"
        }
    }
    """
    method = request.get("method")
    params = request.get("params", {})
    request_id = request.get("id")

    if method != "tasks/cancel":
        raise HTTPException(status_code=400, detail=f"Unknown method: {method}")

    task_id = params.get("task_id")
    if not task_id:
        raise HTTPException(status_code=400, detail="task_id is required")

    if task_id not in a2a_tasks:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    task = a2a_tasks[task_id]
    if task["status"] in ("completed", "cancelled", "failed"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel task in {task['status']} state",
        )

    # Update task status
    task["status"] = "cancelled"
    task["updated_at"] = datetime.now().isoformat()
    task["updates"].append({
        "type": "status_change",
        "status": "cancelled",
        "reason": params.get("reason"),
        "timestamp": datetime.now().isoformat(),
    })

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "task_id": task_id,
            "status": "cancelled",
            "message": "Task cancelled successfully",
        },
    }


# ── A2A Capability Negotiation ────────────────────────────────────────────────

@router.post("/capabilities/query", tags=["A2A"])
async def query_capabilities(request: dict):
    """
    Query this FTE's capabilities for task delegation decisions.
    
    Other FTEs use this to determine if we can handle a task
    before delegating it.
    """
    return {
        "jsonrpc": "2.0",
        "id": request.get("id"),
        "result": {
            "agent": await get_agent_card(),
            "available_skills": [
                {
                    "id": skill["id"],
                    "description": skill["description"],
                    "available": True,
                }
                for skill in await get_agent_card()["skills"]
            ],
            "current_load": {
                "active_tasks": len([t for t in a2a_tasks.values() if t["status"] == "accepted"]),
                "completed_tasks": len([t for t in a2a_tasks.values() if t["status"] == "completed"]),
            },
        },
    }


# ── A2A Streaming Updates (SSE) ───────────────────────────────────────────────

async def task_update_stream(task_id: str):
    """
    Server-Sent Events stream for task updates.
    
    Yields task status updates as they occur.
    """
    import asyncio
    
    last_update_count = 0
    
    while True:
        if task_id not in a2a_tasks:
            yield f"event: error\ndata: {{\"error\": \"Task not found\"}}\n\n"
            break
        
        task = a2a_tasks[task_id]
        new_updates = task["updates"][last_update_count:]
        
        for update in new_updates:
            import json
            yield f"event: update\ndata: {json.dumps(update)}\n\n"
            last_update_count += 1
        
        # Check if task is terminal
        if task["status"] in ("completed", "failed", "cancelled"):
            import json
            yield f"event: {task['status']}\ndata: {json.dumps(task)}\n\n"
            break
        
        await asyncio.sleep(1)  # Poll every second


@router.get("/tasks/{task_id}/stream", tags=["A2A"])
async def stream_task_updates(task_id: str):
    """
    Subscribe to real-time task updates via Server-Sent Events.
    
    Other FTEs can subscribe to this endpoint to receive
    streaming updates on task progress.
    """
    if task_id not in a2a_tasks:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
    
    return StreamingResponse(
        task_update_stream(task_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── A2A Health and Status ─────────────────────────────────────────────────────

@router.get("/status", tags=["A2A"])
async def a2a_status():
    """Get A2A protocol status and statistics."""
    return {
        "protocol": "A2A",
        "version": "1.0.0",
        "status": "active",
        "statistics": {
            "total_tasks_received": len(a2a_tasks),
            "tasks_by_status": {
                status: len([t for t in a2a_tasks.values() if t["status"] == status])
                for status in ["accepted", "completed", "failed", "cancelled"]
            },
            "registered_ftes": len(fte_registry),
        },
    }
