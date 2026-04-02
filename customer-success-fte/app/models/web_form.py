"""Pydantic schemas for the web support form channel."""

import uuid
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class WebFormSubmission(BaseModel):
    """Payload submitted by the Next.js web support form."""

    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: str | None = Field(default=None, pattern=r"^\+?[1-9]\d{6,14}$")
    company: str | None = None
    subject: str = Field(..., min_length=1, max_length=512)
    message: str = Field(..., min_length=1, max_length=10_000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class WebFormResponse(BaseModel):
    """Returned immediately to the form on successful intake."""

    ticket_id: uuid.UUID
    message: str = "Your message has been received. We will be in touch shortly."
