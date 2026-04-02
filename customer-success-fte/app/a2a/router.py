"""
A2A Protocol FastAPI Router

This router exposes the A2A protocol endpoints for inter-FTE communication.
"""

import logging
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request, Response

from app.a2a.protocol import (
    A2AServer,
    A2AMessage,
    MessageType,
    FTEType,
    HandoffReason,
    HandoffRequest,
    ConversationContext,
    create_a2a_server,
)
from app.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/a2a", tags=["A2A Protocol"])

# Global A2A server instance
_a2a_server: A2AServer | None = None


def get_a2a_server() -> A2AServer:
    """Get or create the A2A server instance"""
    global _a2a_server
    if _a2a_server is None:
        settings = get_settings()
        _a2a_server = create_a2a_server(
            fte_id=settings.fte_id,
            fte_type="customer-success",
            api_key=settings.a2a_api_key,
        )
    return _a2a_server


@router.post("")
async def handle_a2a_message(
    request: Request,
    x_a2a_protocol_version: str = Header(default="1.0.0"),
    x_a2a_sender_id: str = Header(...),
    x_a2a_sender_type: str = Header(...),
) -> dict[str, Any]:
    """
    Handle incoming A2A protocol messages.
    
    This endpoint receives messages from other FTEs for:
    - Handoff requests
    - Collaboration requests
    - Status queries
    - Heartbeats
    """
    
    try:
        message_data = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
    
    server = get_a2a_server()
    
    try:
        response_message = await server.handle_message(message_data)
        return response_message.to_dict()
        
    except Exception as e:
        logger.exception(f"Error processing A2A message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """A2A endpoint health check"""
    return {
        "status": "healthy",
        "protocol_version": A2A_PROTOCOL_VERSION,
        "fte_id": get_settings().fte_id,
        "fte_type": "customer-success",
    }


@router.post("/handoff/request")
async def request_handoff(
    target_fte_type: str,
    reason: str,
    reason_description: str,
    conversation_id: str,
    customer_id: str,
    priority: str = "normal",
) -> dict[str, Any]:
    """
    Request a handoff to another FTE.
    
    This endpoint initiates a handoff to another FTE type.
    """
    
    from app.a2a.protocol import A2AClient, FTEAddress
    
    settings = get_settings()
    client = A2AClient(
        fte_id=settings.fte_id,
        fte_type=FTEType.CUSTOMER_SUCCESS,
        api_key=settings.a2a_api_key,
    )
    
    # Find target FTE
    # In production, this would query a service registry
    target_fte = client.get_fte_by_type(FTEType(target_fte_type))
    
    if not target_fte:
        return {
            "accepted": False,
            "rejection_reason": f"No FTE of type {target_fte_type} found",
        }
    
    # Create conversation context
    conversation_context = ConversationContext(
        conversation_id=conversation_id,
        customer_id=customer_id,
    )
    
    # Create handoff request
    handoff_request = HandoffRequest(
        reason=HandoffReason(reason),
        reason_description=reason_description,
        priority=priority,
    )
    
    try:
        response = await client.request_handoff(
            target_fte=target_fte,
            conversation_context=conversation_context,
            handoff_request=handoff_request,
        )
        
        return response.to_dict()
        
    finally:
        await client.close()


@router.post("/collaboration/request")
async def request_collaboration(
    target_fte_type: str,
    conversation_id: str,
    customer_id: str,
    collaboration_type: str,
    request_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Request collaboration from another FTE.
    
    This endpoint requests assistance from another FTE without a full handoff.
    """
    
    from app.a2a.protocol import A2AClient, FTEAddress
    
    settings = get_settings()
    client = A2AClient(
        fte_id=settings.fte_id,
        fte_type=FTEType.CUSTOMER_SUCCESS,
        api_key=settings.a2a_api_key,
    )
    
    # Find target FTE
    target_fte = client.get_fte_by_type(FTEType(target_fte_type))
    
    if not target_fte:
        return {
            "status": "error",
            "message": f"No FTE of type {target_fte_type} found",
        }
    
    # Create conversation context
    conversation_context = ConversationContext(
        conversation_id=conversation_id,
        customer_id=customer_id,
    )
    
    try:
        response = await client.request_collaboration(
            target_fte=target_fte,
            conversation_context=conversation_context,
            collaboration_request={
                "type": collaboration_type,
                **request_data,
            },
        )
        
        return response
        
    finally:
        await client.close()


@router.get("/ftes")
async def list_known_ftes() -> dict[str, Any]:
    """List all known FTE instances"""
    
    server = get_a2a_server()
    
    return {
        "ftes": [
            {
                "fte_id": fte.fte_id,
                "fte_type": fte.fte_type.value,
                "url": fte.url,
            }
            for fte in server.client.known_ftes.values()
        ]
    }


@router.post("/ftes/register")
async def register_fte(
    fte_id: str,
    fte_type: str,
    host: str,
    port: int,
    protocol: str = "http",
) -> dict[str, Any]:
    """Register a known FTE instance"""
    
    from app.a2a.protocol import FTEAddress
    
    server = get_a2a_server()
    
    fte = FTEAddress(
        fte_id=fte_id,
        fte_type=FTEType(fte_type),
        host=host,
        port=port,
        protocol=protocol,
    )
    
    server.client.register_fte(fte)
    
    return {
        "status": "registered",
        "fte_id": fte_id,
        "fte_type": fte_type,
    }
