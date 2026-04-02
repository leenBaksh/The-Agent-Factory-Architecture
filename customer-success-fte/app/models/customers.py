"""Pydantic schemas for customer-related endpoints."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class CustomerCreate(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, pattern=r"^\+?[1-9]\d{6,14}$")
    company: str | None = None
    plan: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CustomerRead(BaseModel):
    id: uuid.UUID
    display_name: str
    email: str | None
    phone: str | None
    company: str | None
    plan: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
