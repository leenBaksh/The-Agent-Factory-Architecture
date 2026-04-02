"""
A2A (Agent-to-Agent) Protocol Implementation

This module implements the inter-FTE collaboration protocol for communication between
different Digital FTE instances. It enables seamless handoffs and collaboration between
specialized agents (e.g., Customer Success FTE → Sales FTE → Technical Support FTE).

Protocol Layers:
1. Transport: HTTP/gRPC with Dapr service invocation
2. Message: JSON-RPC 2.0 inspired format
3. Session: Conversation context preservation across FTE boundaries
4. Security: mTLS + JWT authentication between FTEs
"""

import asyncio
import hashlib
import hmac
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


# ── Protocol Constants ─────────────────────────────────────────────────────────

A2A_PROTOCOL_VERSION = "1.0.0"
DEFAULT_TIMEOUT_SECONDS = 30.0
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 1.0


class MessageType(Enum):
    """A2A message types"""
    HANDOFF_REQUEST = "handoff_request"
    HANDOFF_ACCEPT = "handoff_accept"
    HANDOFF_REJECT = "handoff_reject"
    COLLABORATION_REQUEST = "collaboration_request"
    COLLABORATION_RESPONSE = "collaboration_response"
    STATUS_QUERY = "status_query"
    STATUS_RESPONSE = "status_response"
    HEARTBEAT = "heartbeat"
    SHUTDOWN = "shutdown"


class HandoffReason(Enum):
    """Reasons for FTE handoff"""
    ESCALATION = "escalation"
    SPECIALIZATION = "specialization"
    CAPACITY = "capacity"
    SCHEDULE = "schedule"
    CUSTOMER_REQUEST = "customer_request"


class FTEType(Enum):
    """Known FTE types"""
    CUSTOMER_SUCCESS = "customer-success"
    SALES = "sales"
    TECHNICAL_SUPPORT = "technical-support"
    BILLING = "billing"
    HR = "hr"
    GENERAL = "general"


# ── Data Classes ──────────────────────────────────────────────────────────────

@dataclass
class FTEAddress:
    """Network address of an FTE instance"""
    fte_id: str
    fte_type: FTEType
    host: str
    port: int
    protocol: str = "http"
    version: str = "1.0.0"
    
    @property
    def url(self) -> str:
        return f"{self.protocol}://{self.host}:{self.port}"
    
    @property
    def a2a_endpoint(self) -> str:
        return f"{self.url}/api/a2a"


@dataclass
class ConversationContext:
    """Conversation context for handoffs"""
    conversation_id: str
    customer_id: str
    message_history: list[dict[str, Any]] = field(default_factory=list)
    current_ticket_id: Optional[str] = None
    sentiment_score: float = 0.5
    urgency_level: str = "normal"
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "customer_id": self.customer_id,
            "message_history": self.message_history,
            "current_ticket_id": self.current_ticket_id,
            "sentiment_score": self.sentiment_score,
            "urgency_level": self.urgency_level,
            "tags": self.tags,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConversationContext":
        return cls(**data)


@dataclass
class A2AMessage:
    """A2A protocol message"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    message_type: MessageType = MessageType.HEARTBEAT
    sender_fte_id: str = ""
    sender_fte_type: str = ""
    recipient_fte_id: Optional[str] = None
    recipient_fte_type: Optional[str] = None
    conversation_context: Optional[ConversationContext] = None
    payload: dict[str, Any] = field(default_factory=dict)
    signature: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id,
            "timestamp": self.timestamp,
            "version": A2A_PROTOCOL_VERSION,
            "message_type": self.message_type.value,
            "sender": {
                "fte_id": self.sender_fte_id,
                "fte_type": self.sender_fte_type,
            },
            "recipient": {
                "fte_id": self.recipient_fte_id,
                "fte_type": self.recipient_fte_type,
            } if self.recipient_fte_id else None,
            "conversation_context": self.conversation_context.to_dict() if self.conversation_context else None,
            "payload": self.payload,
            "signature": self.signature,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "A2AMessage":
        conversation_context = None
        if data.get("conversation_context"):
            conversation_context = ConversationContext.from_dict(data["conversation_context"])
        
        return cls(
            message_id=data["message_id"],
            timestamp=data["timestamp"],
            message_type=MessageType(data["message_type"]),
            sender_fte_id=data["sender"]["fte_id"],
            sender_fte_type=data["sender"]["fte_type"],
            recipient_fte_id=data.get("recipient", {}).get("fte_id") if data.get("recipient") else None,
            recipient_fte_type=data.get("recipient", {}).get("fte_type") if data.get("recipient") else None,
            conversation_context=conversation_context,
            payload=data.get("payload", {}),
            signature=data.get("signature"),
        )


@dataclass
class HandoffRequest:
    """Handoff request payload"""
    reason: HandoffReason
    reason_description: str
    priority: str = "normal"
    required_capabilities: list[str] = field(default_factory=list)
    deadline: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "reason": self.reason.value,
            "reason_description": self.reason_description,
            "priority": self.priority,
            "required_capabilities": self.required_capabilities,
            "deadline": self.deadline,
        }


@dataclass
class HandoffResponse:
    """Handoff response payload"""
    accepted: bool
    recipient_fte_id: Optional[str] = None
    recipient_fte_type: Optional[str] = None
    rejection_reason: Optional[str] = None
    estimated_wait_minutes: Optional[int] = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "recipient_fte_id": self.recipient_fte_id,
            "recipient_fte_type": self.recipient_fte_type,
            "rejection_reason": self.rejection_reason,
            "estimated_wait_minutes": self.estimated_wait_minutes,
        }


# ── A2A Client ─────────────────────────────────────────────────────────────────

class A2AClient:
    """Client for A2A protocol communication"""
    
    def __init__(
        self,
        fte_id: str,
        fte_type: FTEType,
        api_key: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ):
        self.fte_id = fte_id
        self.fte_type = fte_type
        self.api_key = api_key
        self.timeout = timeout
        self.http_client = httpx.AsyncClient(timeout=timeout)
        self.known_ftes: dict[str, FTEAddress] = {}
    
    async def close(self):
        await self.http_client.aclose()
    
    def _sign_message(self, message: A2AMessage, secret: str) -> str:
        """Sign a message for authentication"""
        message_data = json.dumps(message.to_dict(), sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            message_data.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _verify_message(self, message: A2AMessage, secret: str) -> bool:
        """Verify message signature"""
        if not message.signature:
            return False
        
        expected_signature = self._sign_message(message, secret)
        return hmac.compare_digest(message.signature, expected_signature)
    
    async def _send_message(
        self,
        message: A2AMessage,
        endpoint: str,
        retry_count: int = 0
    ) -> A2AMessage:
        """Send an A2A message with retry logic"""
        
        # Sign the message
        if self.api_key:
            message.signature = self._sign_message(message, self.api_key)
        
        try:
            response = await self.http_client.post(
                endpoint,
                json=message.to_dict(),
                headers={
                    "Content-Type": "application/json",
                    "X-A2A-Protocol-Version": A2A_PROTOCOL_VERSION,
                    "X-A2A-Sender-ID": self.fte_id,
                    "X-A2A-Sender-Type": self.fte_type.value,
                }
            )
            response.raise_for_status()
            
            response_message = A2AMessage.from_dict(response.json())
            
            # Verify signature if API key is set
            if self.api_key and response_message.signature:
                if not self._verify_message(response_message, self.api_key):
                    raise ValueError("Invalid message signature")
            
            return response_message
            
        except httpx.HTTPError as e:
            if retry_count < MAX_RETRIES:
                logger.warning(
                    f"A2A request failed, retrying in {RETRY_DELAY_SECONDS}s: {e}"
                )
                await asyncio.sleep(RETRY_DELAY_SECONDS)
                return await self._send_message(message, endpoint, retry_count + 1)
            raise
    
    async def request_handoff(
        self,
        target_fte: FTEAddress,
        conversation_context: ConversationContext,
        handoff_request: HandoffRequest,
    ) -> HandoffResponse:
        """Request a handoff to another FTE"""
        
        message = A2AMessage(
            message_type=MessageType.HANDOFF_REQUEST,
            sender_fte_id=self.fte_id,
            sender_fte_type=self.fte_type.value,
            recipient_fte_id=target_fte.fte_id,
            recipient_fte_type=target_fte.fte_type.value,
            conversation_context=conversation_context,
            payload=handoff_request.to_dict(),
        )
        
        response = await self._send_message(message, target_fte.a2a_endpoint)
        
        if response.message_type == MessageType.HANDOFF_ACCEPT:
            return HandoffResponse(
                accepted=True,
                recipient_fte_id=response.sender_fte_id,
                recipient_fte_type=response.sender_fte_type,
                estimated_wait_minutes=response.payload.get("estimated_wait_minutes"),
            )
        elif response.message_type == MessageType.HANDOFF_REJECT:
            return HandoffResponse(
                accepted=False,
                rejection_reason=response.payload.get("reason"),
            )
        else:
            raise ValueError(f"Unexpected response type: {response.message_type}")
    
    async def request_collaboration(
        self,
        target_fte: FTEAddress,
        conversation_context: ConversationContext,
        collaboration_request: dict[str, Any],
    ) -> dict[str, Any]:
        """Request collaboration from another FTE"""
        
        message = A2AMessage(
            message_type=MessageType.COLLABORATION_REQUEST,
            sender_fte_id=self.fte_id,
            sender_fte_type=self.fte_type.value,
            recipient_fte_id=target_fte.fte_id,
            recipient_fte_type=target_fte.fte_type.value,
            conversation_context=conversation_context,
            payload=collaboration_request,
        )
        
        response = await self._send_message(message, target_fte.a2a_endpoint)
        
        if response.message_type == MessageType.COLLABORATION_RESPONSE:
            return response.payload
        else:
            raise ValueError(f"Unexpected response type: {response.message_type}")
    
    async def send_heartbeat(self, target_fte: FTEAddress) -> bool:
        """Send heartbeat to check FTE availability"""
        
        message = A2AMessage(
            message_type=MessageType.HEARTBEAT,
            sender_fte_id=self.fte_id,
            sender_fte_type=self.fte_type.value,
            recipient_fte_id=target_fte.fte_id,
            recipient_fte_type=target_fte.fte_type.value,
        )
        
        try:
            response = await self._send_message(message, target_fte.a2a_endpoint)
            return response.message_type == MessageType.HEARTBEAT
        except Exception:
            return False
    
    def register_fte(self, fte: FTEAddress):
        """Register a known FTE address"""
        self.known_ftes[fte.fte_id] = fte
    
    def get_fte_by_type(self, fte_type: FTEType) -> Optional[FTEAddress]:
        """Get an FTE address by type"""
        for fte in self.known_ftes.values():
            if fte.fte_type == fte_type:
                return fte
        return None


# ── A2A Server ─────────────────────────────────────────────────────────────────

class A2AServer:
    """Server for handling incoming A2A requests"""
    
    def __init__(
        self,
        fte_id: str,
        fte_type: FTEType,
        api_key: Optional[str] = None,
    ):
        self.fte_id = fte_id
        self.fte_type = fte_type
        self.api_key = api_key
        self.handlers: dict[MessageType, callable] = {}
        self.client = A2AClient(fte_id, fte_type, api_key)
    
    def register_handler(self, message_type: MessageType, handler: callable):
        """Register a handler for a message type"""
        self.handlers[message_type] = handler
    
    async def handle_message(self, message_data: dict[str, Any]) -> A2AMessage:
        """Handle an incoming A2A message"""
        
        message = A2AMessage.from_dict(message_data)
        
        # Verify signature
        if self.api_key and message.signature:
            if not self.client._verify_message(message, self.api_key):
                return A2AMessage(
                    message_type=MessageType.HANDOFF_REJECT,
                    sender_fte_id=self.fte_id,
                    sender_fte_type=self.fte_type.value,
                    recipient_fte_id=message.sender_fte_id,
                    payload={"reason": "Invalid signature"},
                )
        
        # Get handler for message type
        handler = self.handlers.get(message.message_type)
        
        if not handler:
            return A2AMessage(
                message_type=MessageType.HANDOFF_REJECT,
                sender_fte_id=self.fte_id,
                sender_fte_type=self.fte_type.value,
                recipient_fte_id=message.sender_fte_id,
                payload={"reason": f"Unsupported message type: {message.message_type.value}"},
            )
        
        try:
            response = await handler(message)
            return response
        except Exception as e:
            logger.exception(f"Error handling A2A message: {e}")
            return A2AMessage(
                message_type=MessageType.HANDOFF_REJECT,
                sender_fte_id=self.fte_id,
                sender_fte_type=self.fte_type.value,
                recipient_fte_id=message.sender_fte_id,
                payload={"reason": str(e)},
            )
    
    async def handle_handoff_request(self, message: A2AMessage) -> A2AMessage:
        """Handle incoming handoff request"""
        
        # Default implementation - override in subclass
        return A2AMessage(
            message_type=MessageType.HANDOFF_REJECT,
            sender_fte_id=self.fte_id,
            sender_fte_type=self.fte_type.value,
            recipient_fte_id=message.sender_fte_id,
            payload={"reason": "Handoff not implemented"},
        )
    
    async def handle_collaboration_request(self, message: A2AMessage) -> A2AMessage:
        """Handle incoming collaboration request"""
        
        # Default implementation - override in subclass
        return A2AMessage(
            message_type=MessageType.COLLABORATION_RESPONSE,
            sender_fte_id=self.fte_id,
            sender_fte_type=self.fte_type.value,
            recipient_fte_id=message.sender_fte_id,
            payload={"status": "not_implemented"},
        )
    
    async def handle_heartbeat(self, message: A2AMessage) -> A2AMessage:
        """Handle heartbeat"""
        
        return A2AMessage(
            message_type=MessageType.HEARTBEAT,
            sender_fte_id=self.fte_id,
            sender_fte_type=self.fte_type.value,
            recipient_fte_id=message.sender_fte_id,
            payload={"status": "healthy"},
        )


# ── FTE Registry (Service Discovery) ──────────────────────────────────────────

class FTERegistry:
    """Service registry for FTE discovery"""
    
    def __init__(self):
        self.ftes: dict[str, FTEAddress] = {}
        self.health_checks: dict[str, float] = {}
    
    def register(self, fte: FTEAddress):
        """Register an FTE"""
        self.ftes[fte.fte_id] = fte
        self.health_checks[fte.fte_id] = time.time()
        logger.info(f"Registered FTE: {fte.fte_id} ({fte.fte_type.value})")
    
    def unregister(self, fte_id: str):
        """Unregister an FTE"""
        if fte_id in self.ftes:
            del self.ftes[fte_id]
            del self.health_checks[fte_id]
            logger.info(f"Unregistered FTE: {fte_id}")
    
    def get_by_type(self, fte_type: FTEType) -> list[FTEAddress]:
        """Get all FTEs of a specific type"""
        return [fte for fte in self.ftes.values() if fte.fte_type == fte_type]
    
    def get_healthy_ftes(self, max_age_seconds: int = 60) -> list[FTEAddress]:
        """Get FTEs that have sent a heartbeat recently"""
        cutoff = time.time() - max_age_seconds
        return [
            self.ftes[fte_id]
            for fte_id, last_heartbeat in self.health_checks.items()
            if last_heartbeat > cutoff
        ]
    
    def update_heartbeat(self, fte_id: str):
        """Update heartbeat for an FTE"""
        self.health_checks[fte_id] = time.time()


# ── Factory Functions ──────────────────────────────────────────────────────────

def create_a2a_client(
    fte_id: str,
    fte_type: str,
    api_key: Optional[str] = None,
) -> A2AClient:
    """Create an A2A client instance"""
    return A2AClient(
        fte_id=fte_id,
        fte_type=FTEType(fte_type),
        api_key=api_key,
    )


def create_a2a_server(
    fte_id: str,
    fte_type: str,
    api_key: Optional[str] = None,
) -> A2AServer:
    """Create an A2A server instance"""
    server = A2AServer(
        fte_id=fte_id,
        fte_type=FTEType(fte_type),
        api_key=api_key,
    )
    
    # Register default handlers
    server.register_handler(MessageType.HANDOFF_REQUEST, server.handle_handoff_request)
    server.register_handler(MessageType.COLLABORATION_REQUEST, server.handle_collaboration_request)
    server.register_handler(MessageType.HEARTBEAT, server.handle_heartbeat)
    
    return server
