"""Pydantic schemas for ticket-related endpoints."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.database import TicketPriority, TicketStatus


class TicketCreate(BaseModel):
    subject: str = Field(..., min_length=1, max_length=512)
    description: str | None = None
    category: str | None = None
    priority: TicketPriority = TicketPriority.medium
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TicketUpdate(BaseModel):
    subject: str | None = Field(default=None, min_length=1, max_length=512)
    description: str | None = None
    category: str | None = None
    status: TicketStatus | None = None
    priority: TicketPriority | None = None
    assigned_to: str | None = None
    resolution: str | None = None
    tags: list[str] | None = None


class TicketRead(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    customer_id: uuid.UUID
    subject: str
    description: str | None
    category: str | None
    status: TicketStatus
    priority: TicketPriority
    assigned_to: str | None
    resolution: str | None
    tags: list[str]
    escalated_at: datetime | None
    resolved_at: datetime | None
    closed_at: datetime | None
    due_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
