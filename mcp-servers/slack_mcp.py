"""
Slack MCP Server for Digital FTEs

Provides tool access for:
- Sending messages to channels
- Reading channel messages
- Managing threads
- Posting alerts and notifications
"""

import os
import logging
from typing import Optional
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    "slack-server",
    description="Slack integration for team communication and alerts",
    dependencies=["slack-sdk"],
)

# Global Slack client
slack_client: Optional[WebClient] = None


@asynccontextmanager
async def get_slack_client():
    """Get authenticated Slack client."""
    global slack_client
    if slack_client is None:
        token = os.getenv("SLACK_BOT_TOKEN")
        if not token:
            raise ValueError("SLACK_BOT_TOKEN environment variable not set")
        slack_client = WebClient(token=token)
    yield slack_client


@mcp.tool()
async def send_message(
    channel: str,
    message: str,
    thread_ts: Optional[str] = None,
) -> dict:
    """
    Send a message to a Slack channel or thread.

    Args:
        channel: Channel name (with #) or ID
        message: Message text to send
        thread_ts: Optional thread timestamp to reply in thread

    Returns:
        dict with message details including ts (timestamp)
    """
    async with get_slack_client() as client:
        try:
            response = client.chat_postMessage(
                channel=channel,
                text=message,
                thread_ts=thread_ts,
            )
            return {
                "success": True,
                "channel": response["channel"],
                "ts": response["ts"],
                "message": response["message"]["text"],
            }
        except SlackApiError as e:
            logger.error(f"Failed to send Slack message: {e}")
            return {"success": False, "error": str(e)}


@mcp.tool()
async def get_channel_messages(
    channel: str,
    limit: int = 10,
    oldest: Optional[str] = None,
    latest: Optional[str] = None,
) -> list[dict]:
    """
    Get recent messages from a Slack channel.

    Args:
        channel: Channel name (with #) or ID
        limit: Number of messages to retrieve (default: 10, max: 100)
        oldest: Optional start timestamp
        latest: Optional end timestamp

    Returns:
        list of message dicts with text, user, timestamp, etc.
    """
    limit = min(limit, 100)  # Enforce max limit

    async with get_slack_client() as client:
        try:
            response = client.conversations_history(
                channel=channel,
                limit=limit,
                oldest=oldest,
                latest=latest,
            )
            return [
                {
                    "ts": msg["ts"],
                    "user": msg.get("user", "unknown"),
                    "text": msg["text"],
                    "thread_ts": msg.get("thread_ts"),
                    "reply_count": msg.get("reply_count", 0),
                }
                for msg in response["messages"]
            ]
        except SlackApiError as e:
            logger.error(f"Failed to get Slack messages: {e}")
            return []


@mcp.tool()
async def post_alert(
    channel: str,
    title: str,
    message: str,
    severity: str = "info",
) -> dict:
    """
    Post a formatted alert to a Slack channel.

    Args:
        channel: Channel name (with #) or ID
        title: Alert title
        message: Alert details
        severity: Alert severity (info, warning, critical)

    Returns:
        dict with alert details
    """
    emoji_map = {
        "info": ":information_source:",
        "warning": ":warning:",
        "critical": ":rotating_light:",
        "success": ":white_check_mark:",
    }

    color_map = {
        "info": "36a64f",
        "warning": "ffaa00",
        "critical": "ff0000",
        "success": "36a64f",
    }

    emoji = emoji_map.get(severity, ":bell:")
    color = color_map.get(severity, "36a64f")

    formatted_message = f"""{emoji} *{title}*

{message}

*Severity:* {severity.upper()}
*Timestamp:* <!(date)^|now>"""

    async with get_slack_client() as client:
        try:
            response = client.chat_postMessage(
                channel=channel,
                blocks=[
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": formatted_message},
                    }
                ],
                attachments=[
                    {
                        "color": color,
                        "blocks": [
                            {
                                "type": "section",
                                "text": {"type": "mrkdwn", "text": message},
                            }
                        ],
                    }
                ],
            )
            return {
                "success": True,
                "channel": response["channel"],
                "ts": response["ts"],
            }
        except SlackApiError as e:
            logger.error(f"Failed to post Slack alert: {e}")
            return {"success": False, "error": str(e)}


@mcp.tool()
async def get_user_info(user_id: str) -> dict:
    """
    Get information about a Slack user.

    Args:
        user_id: Slack user ID

    Returns:
        dict with user details (name, email, display_name, etc.)
    """
    async with get_slack_client() as client:
        try:
            response = client.users_info(user=user_id)
            user = response["user"]
            profile = user.get("profile", {})
            return {
                "id": user["id"],
                "name": user.get("name", "unknown"),
                "display_name": profile.get("display_name", user.get("name", "unknown")),
                "email": profile.get("email"),
                "title": profile.get("title"),
                "real_name": profile.get("real_name"),
            }
        except SlackApiError as e:
            logger.error(f"Failed to get Slack user info: {e}")
            return {}


@mcp.tool()
async def list_channels(
    exclude_archived: bool = True,
    types: list[str] = None,
) -> list[dict]:
    """
    List available Slack channels.

    Args:
        exclude_archived: Whether to exclude archived channels
        types: Channel types to include (default: public_channel)

    Returns:
        list of channel dicts with id, name, purpose
    """
    if types is None:
        types = ["public_channel"]

    async with get_slack_client() as client:
        try:
            response = client.conversations_list(
                exclude_archived=exclude_archived,
                types=types,
                limit=200,
            )
            return [
                {
                    "id": ch["id"],
                    "name": ch["name"],
                    "purpose": ch.get("purpose", {}).get("value", ""),
                    "is_member": ch.get("is_member", False),
                }
                for ch in response["channels"]
            ]
        except SlackApiError as e:
            logger.error(f"Failed to list Slack channels: {e}")
            return []


if __name__ == "__main__":
    mcp.run()
