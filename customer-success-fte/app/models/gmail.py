"""
Pydantic schemas for Gmail push notifications via Cloud Pub/Sub.

Google delivers push notifications as:
  POST body → { "message": { "data": "<base64>", "messageId": "...", "publishTime": "..." },
                "subscription": "projects/.../subscriptions/..." }

The base64-decoded data contains the Gmail historyId that changed.
"""

from pydantic import BaseModel, Field


class PubSubMessage(BaseModel):
    data: str = Field(..., description="Base64-encoded notification payload")
    message_id: str = Field(..., alias="messageId")
    publish_time: str = Field(..., alias="publishTime")
    attributes: dict[str, str] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


class GmailPushNotification(BaseModel):
    """Root payload delivered by Cloud Pub/Sub to our webhook endpoint."""

    message: PubSubMessage
    subscription: str
