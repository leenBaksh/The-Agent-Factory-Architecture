"""
Gmail MCP Server for Digital FTEs

Provides tool access for:
- Reading and sending emails
- Managing labels and threads
- Searching inbox
- Checking unread messages
"""

import os
import logging
import base64
from typing import Optional
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    "gmail-server",
    description="Gmail API integration for email communication",
    dependencies=["google-api-python-client", "google-auth-httplib2", "google-auth-oauthlib"],
)

# Gmail OAuth scopes
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/gmail.modify",
]

# Global Gmail service
gmail_service = None


def get_gmail_service():
    """Get authenticated Gmail service."""
    global gmail_service
    
    if gmail_service is not None:
        return gmail_service
    
    credentials_file = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials/gmail_credentials.json")
    token_file = os.getenv("GMAIL_TOKEN_FILE", "credentials/gmail_token.json")
    
    creds = None
    
    # Load existing token if it exists
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    
    # If no valid credentials, run OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_file):
                raise FileNotFoundError(
                    f"Credentials file not found at {credentials_file}. "
                    "Download from Google Cloud Console."
                )
            
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(token_file, "w") as token:
            token.write(creds.to_json())
    
    gmail_service = build("gmail", "v1", credentials=creds)
    return gmail_service


@mcp.tool()
async def get_unread_emails(
    max_results: int = 10,
) -> list[dict]:
    """
    Get unread emails from Gmail inbox.

    Args:
        max_results: Maximum number of emails to retrieve (default: 10, max: 50)

    Returns:
        list of email dicts with id, subject, sender, date, snippet
    """
    max_results = min(max_results, 50)
    service = get_gmail_service()
    
    try:
        # Search for unread messages
        results = service.users().messages().list(
            userId="me",
            q="is:unread",
            maxResults=max_results,
        ).execute()
        
        messages = results.get("messages", [])
        
        if not messages:
            return []
        
        emails = []
        for msg in messages:
            message = service.users().messages().get(
                userId="me",
                id=msg["id"],
                format="metadata",
                metadataHeaders=["From", "Subject", "Date"],
            ).execute()
            
            headers = message.get("payload", {}).get("headers", [])
            email_data = {
                "id": message["id"],
                "thread_id": message.get("threadId"),
                "snippet": message.get("snippet", ""),
            }
            
            for header in headers:
                if header["name"] == "From":
                    email_data["sender"] = header["value"]
                elif header["name"] == "Subject":
                    email_data["subject"] = header["value"]
                elif header["name"] == "Date":
                    email_data["date"] = header["value"]
            
            emails.append(email_data)
        
        return emails
    except Exception as e:
        logger.error(f"Failed to get unread emails: {e}")
        return []


@mcp.tool()
async def search_emails(
    query: str,
    max_results: int = 10,
) -> list[dict]:
    """
    Search emails in Gmail.

    Args:
        query: Gmail search query (e.g., "from:boss", "subject:invoice", "has:attachment")
        max_results: Maximum results (default: 10, max: 50)

    Returns:
        list of email dicts matching the query
    """
    max_results = min(max_results, 50)
    service = get_gmail_service()
    
    try:
        results = service.users().messages().list(
            userId="me",
            q=query,
            maxResults=max_results,
        ).execute()
        
        messages = results.get("messages", [])
        
        if not messages:
            return []
        
        emails = []
        for msg in messages:
            message = service.users().messages().get(
                userId="me",
                id=msg["id"],
                format="metadata",
                metadataHeaders=["From", "To", "Subject", "Date"],
            ).execute()
            
            headers = message.get("payload", {}).get("headers", [])
            email_data = {
                "id": message["id"],
                "thread_id": message.get("threadId"),
                "snippet": message.get("snippet", ""),
            }
            
            for header in headers:
                if header["name"] == "From":
                    email_data["sender"] = header["value"]
                elif header["name"] == "To":
                    email_data["to"] = header["value"]
                elif header["name"] == "Subject":
                    email_data["subject"] = header["value"]
                elif header["name"] == "Date":
                    email_data["date"] = header["value"]
            
            emails.append(email_data)
        
        return emails
    except Exception as e:
        logger.error(f"Failed to search emails: {e}")
        return []


@mcp.tool()
async def send_email(
    to: str,
    subject: str,
    body: str,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
) -> dict:
    """
    Send an email via Gmail.

    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body (plain text)
        cc: Optional CC recipients (comma-separated)
        bcc: Optional BCC recipients (comma-separated)

    Returns:
        dict with message_id and status
    """
    service = get_gmail_service()
    
    try:
        # Create message
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        
        if cc:
            message["cc"] = cc
        if bcc:
            message["bcc"] = bcc
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        
        # Send
        sent_message = service.users().messages().send(
            userId="me",
            body={"raw": raw_message},
        ).execute()
        
        return {
            "success": True,
            "message_id": sent_message.get("id"),
            "thread_id": sent_message.get("threadId"),
            "to": to,
            "subject": subject,
        }
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_email_detail(
    message_id: str,
) -> dict:
    """
    Get full details of a specific email.

    Args:
        message_id: Gmail message ID

    Returns:
        dict with full email content including body
    """
    service = get_gmail_service()
    
    try:
        message = service.users().messages().get(
            userId="me",
            id=message_id,
            format="full",
        ).execute()
        
        headers = message.get("payload", {}).get("headers", [])
        email_data = {
            "id": message["id"],
            "thread_id": message.get("threadId"),
            "snippet": message.get("snippet", ""),
            "internal_date": message.get("internalDate"),
        }
        
        for header in headers:
            if header["name"] == "From":
                email_data["sender"] = header["value"]
            elif header["name"] == "To":
                email_data["to"] = header["value"]
            elif header["name"] == "Subject":
                email_data["subject"] = header["value"]
            elif header["name"] == "Date":
                email_data["date"] = header["value"]
        
        # Extract body
        body = ""
        if "parts" in message["payload"]:
            for part in message["payload"]["parts"]:
                if part["mimeType"] == "text/plain" and "body" in part:
                    body_data = part["body"].get("data", "")
                    body = base64.urlsafe_b64decode(body_data).decode("utf-8")
                    break
        
        email_data["body"] = body
        
        return email_data
    except Exception as e:
        logger.error(f"Failed to get email detail: {e}")
        return {}


@mcp.tool()
async def mark_as_read(
    message_id: str,
) -> dict:
    """
    Mark an email as read (remove UNREAD label).

    Args:
        message_id: Gmail message ID

    Returns:
        dict with status
    """
    service = get_gmail_service()
    
    try:
        service.users().messages().modify(
            userId="me",
            id=message_id,
            body={"removeLabelIds": ["UNREAD"]},
        ).execute()
        
        return {
            "success": True,
            "message_id": message_id,
            "status": "marked_as_read",
        }
    except Exception as e:
        logger.error(f"Failed to mark as read: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def add_label(
    message_id: str,
    label_name: str,
) -> dict:
    """
    Add a label to an email.

    Args:
        message_id: Gmail message ID
        label_name: Label to add (e.g., "IMPORTANT", "STARRED", or custom label)

    Returns:
        dict with status
    """
    service = get_gmail_service()
    
    try:
        # Find or create label
        labels = service.users().labels().list(userId="me").execute()
        label_id = None
        
        for label in labels.get("labels", []):
            if label["name"].upper() == label_name.upper():
                label_id = label["id"]
                break
        
        if not label_id:
            # Create label
            label_obj = service.users().labels().create(
                userId="me",
                body={"name": label_name, "labelListVisibility": "labelShow", "messageListVisibility": "show"},
            ).execute()
            label_id = label_obj["id"]
        
        # Add label to message
        service.users().messages().modify(
            userId="me",
            id=message_id,
            body={"addLabelIds": [label_id]},
        ).execute()
        
        return {
            "success": True,
            "message_id": message_id,
            "label": label_name,
        }
    except Exception as e:
        logger.error(f"Failed to add label: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_inbox_stats() -> dict:
    """
    Get inbox statistics.

    Returns:
        dict with unread count, total count, and labeled counts
    """
    service = get_gmail_service()
    
    try:
        # Get unread count
        unread = service.users().messages().list(
            userId="me",
            q="is:unread",
            maxResults=1,
        ).execute()
        unread_count = unread.get("resultSizeEstimate", 0)
        
        # Get total count
        total = service.users().messages().list(
            userId="me",
            maxResults=1,
        ).execute()
        total_count = total.get("resultSizeEstimate", 0)
        
        # Get starred count
        starred = service.users().messages().list(
            userId="me",
            q="is:starred",
            maxResults=1,
        ).execute()
        starred_count = starred.get("resultSizeEstimate", 0)
        
        return {
            "unread": unread_count,
            "total": total_count,
            "starred": starred_count,
        }
    except Exception as e:
        logger.error(f"Failed to get inbox stats: {e}")
        return {}


if __name__ == "__main__":
    mcp.run()
