"""
Pydantic schemas for WhatsApp Cloud API webhooks (Meta).

Meta delivers events in this structure:
  {
    "object": "whatsapp_business_account",
    "entry": [{
      "id": "<WABA_ID>",
      "changes": [{
        "value": {
          "messaging_product": "whatsapp",
          "metadata": { "display_phone_number": "...", "phone_number_id": "..." },
          "messages": [{ "from": "15551234567", "id": "...", "timestamp": "...",
                         "text": { "body": "Hello" }, "type": "text" }],
          "statuses": [...]
        },
        "field": "messages"
      }]
    }]
  }

NOTE: "from" is a Python keyword. The field is declared with alias="from" so
Pydantic maps the JSON key correctly; access it via msg.sender in Python.
"""

from pydantic import BaseModel, Field, StringConstraints
from typing import Annotated

# Max lengths based on WhatsApp API limits
MAX_PHONE_NUMBER_LENGTH = 20
MAX_MESSAGE_ID_LENGTH = 100
MAX_MESSAGE_BODY_LENGTH = 4096
MAX_TIMESTAMP_LENGTH = 50
MAX_STATUS_LENGTH = 50


class WhatsAppMetadata(BaseModel):
    display_phone_number: Annotated[str, StringConstraints(max_length=MAX_PHONE_NUMBER_LENGTH)]
    phone_number_id: Annotated[str, StringConstraints(max_length=MAX_PHONE_NUMBER_LENGTH)]


class WhatsAppTextBody(BaseModel):
    body: Annotated[str, StringConstraints(max_length=MAX_MESSAGE_BODY_LENGTH)]


class WhatsAppImageBody(BaseModel):
    caption: Annotated[str, StringConstraints(max_length=MAX_MESSAGE_BODY_LENGTH)] = ""
    mime_type: str = ""
    sha256: str = ""
    id: str = ""


class WhatsAppMessage(BaseModel):
    """Single message event from Meta. Sender phone lives in `sender`."""

    model_config = {"populate_by_name": True}

    sender: Annotated[str, Field(..., alias="from", max_length=MAX_PHONE_NUMBER_LENGTH)]
    id: Annotated[str, StringConstraints(max_length=MAX_MESSAGE_ID_LENGTH)]
    timestamp: Annotated[str, StringConstraints(max_length=MAX_TIMESTAMP_LENGTH)]
    type: str
    text: WhatsAppTextBody | None = None
    image: WhatsAppImageBody | None = None       # stub for future media handling


class WhatsAppStatus(BaseModel):
    id: Annotated[str, StringConstraints(max_length=MAX_MESSAGE_ID_LENGTH)]
    status: Annotated[str, StringConstraints(max_length=MAX_STATUS_LENGTH)]
    timestamp: Annotated[str, StringConstraints(max_length=MAX_TIMESTAMP_LENGTH)]
    recipient_id: Annotated[str, StringConstraints(max_length=MAX_PHONE_NUMBER_LENGTH)]


class WhatsAppChangeValue(BaseModel):
    messaging_product: str
    metadata: WhatsAppMetadata
    messages: list[WhatsAppMessage] = []
    statuses: list[WhatsAppStatus] = []


class WhatsAppChange(BaseModel):
    value: WhatsAppChangeValue
    field: str


class WhatsAppEntry(BaseModel):
    id: Annotated[str, StringConstraints(max_length=MAX_MESSAGE_ID_LENGTH)]
    changes: list[WhatsAppChange]


class WhatsAppWebhookPayload(BaseModel):
    """Root payload from Meta WhatsApp Cloud API."""

    object: Annotated[str, StringConstraints(max_length=100)]
    entry: list[WhatsAppEntry]
