"""
Gmail API service.

Wraps the Google Gmail v1 REST API with:
  - OAuth2 credential loading and auto-refresh
  - History.list() → Messages.get() pipeline
  - MIME parsing (plain-text extraction, sender/subject parsing)
  - Async interface via thread-pool executor (google-api-python-client is sync)

Dependencies:
    google-api-python-client
    google-auth
    google-auth-httplib2
    google-auth-oauthlib
"""

import asyncio
import base64
import email.utils
import logging
import os
from dataclasses import dataclass
from functools import partial

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# gmail.modify = read + send + label; required for both receiving and replying
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


@dataclass
class ParsedEmail:
    """Normalised email extracted from a Gmail API message object."""

    gmail_id: str
    thread_id: str
    sender_email: str
    sender_name: str
    subject: str
    body: str
    raw_headers: dict[str, str]


# ── Gmail API client ───────────────────────────────────────────────────────────


class GmailService:
    """
    Lazy-initialised Gmail API client.

    The service is built once on first use and cached. Credentials are
    refreshed automatically if they have a valid refresh_token.
    """

    def __init__(self) -> None:
        self._service = None

    # ── Credential management ──────────────────────────────────────────────────

    def _load_credentials(self) -> Credentials:
        token_file = settings.gmail_token_file
        creds_file = settings.gmail_credentials_file

        creds: Credentials | None = None

        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)

        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(token_file, "w") as fh:
                    fh.write(creds.to_json())
                # Secure the token file: owner read/write only
                os.chmod(token_file, 0o600)
                logger.info("Gmail OAuth token refreshed and saved.")
            except Exception as exc:
                logger.error("Failed to refresh Gmail token: %s", exc)
                raise

        if not creds or not creds.valid:
            raise RuntimeError(
                f"Gmail credentials are missing or invalid. "
                f"Run the OAuth consent flow to create {token_file}."
            )

        return creds

    def _build_service(self):
        creds = self._load_credentials()
        return build("gmail", "v1", credentials=creds, cache_discovery=False)

    @property
    def service(self):
        if self._service is None:
            self._service = self._build_service()
        return self._service

    # ── API calls (synchronous — run in thread pool) ───────────────────────────

    def _fetch_new_messages_sync(self, history_id: str) -> list[ParsedEmail]:
        """
        Fetches all messages added to INBOX since `history_id`.

        Calls:
          1. users.history.list(startHistoryId, historyTypes=messageAdded)
          2. users.messages.get(id, format=full) for each new message
        """
        try:
            history_resp = (
                self.service.users()
                .history()
                .list(
                    userId="me",
                    startHistoryId=history_id,
                    historyTypes=["messageAdded"],
                    labelId="INBOX",
                )
                .execute()
            )
        except HttpError as exc:
            logger.error(
                "Gmail History API error (historyId=%s): %s", history_id, exc
            )
            raise

        parsed: list[ParsedEmail] = []
        for record in history_resp.get("history", []):
            for added in record.get("messagesAdded", []):
                msg_id = added["message"]["id"]
                try:
                    raw_msg = (
                        self.service.users()
                        .messages()
                        .get(userId="me", id=msg_id, format="full")
                        .execute()
                    )
                    parsed.append(self._parse_message(raw_msg))
                    logger.debug("Fetched Gmail message id=%s", msg_id)
                except HttpError as exc:
                    logger.warning(
                        "Could not fetch Gmail message id=%s: %s", msg_id, exc
                    )

        logger.info(
            "Gmail history fetch complete: historyId=%s, messages=%d",
            history_id,
            len(parsed),
        )
        return parsed

    # ── MIME parsing ───────────────────────────────────────────────────────────

    def _parse_message(self, raw: dict) -> ParsedEmail:
        """Extract structured fields from a Gmail API message resource."""
        payload = raw.get("payload", {})
        headers = {
            h["name"].lower(): h["value"]
            for h in payload.get("headers", [])
        }

        raw_from = headers.get("from", "")
        sender_name, sender_email = email.utils.parseaddr(raw_from)
        # parseaddr returns ("", "") if unparseable — fall back to raw string
        if not sender_email:
            sender_email = raw_from
            sender_name = raw_from

        subject = headers.get("subject", "(no subject)").strip()
        body = self._extract_plain_text(payload)

        return ParsedEmail(
            gmail_id=raw["id"],
            thread_id=raw.get("threadId", ""),
            sender_email=sender_email.lower(),
            sender_name=sender_name,
            subject=subject,
            body=body,
            raw_headers=headers,
        )

    def _extract_plain_text(self, payload: dict) -> str:
        """
        Recursively extract the first text/plain part from a MIME payload.
        Falls back to text/html if no plain part is found.
        """
        body = self._find_part(payload, "text/plain")
        if not body:
            body = self._find_part(payload, "text/html")
        return body

    def _find_part(self, payload: dict, mime_type: str) -> str:
        """Depth-first search for a MIME part matching `mime_type`."""
        if payload.get("mimeType") == mime_type:
            data = payload.get("body", {}).get("data", "")
            if data:
                # Gmail uses URL-safe base64; pad to a multiple of 4
                padded = data + "=" * (-len(data) % 4)
                return base64.urlsafe_b64decode(padded).decode(
                    "utf-8", errors="replace"
                )

        for part in payload.get("parts", []):
            result = self._find_part(part, mime_type)
            if result:
                return result

        return ""

    # ── Async public interface ─────────────────────────────────────────────────

    async def get_new_messages(self, history_id: str) -> list[ParsedEmail]:
        """
        Async wrapper around `_fetch_new_messages_sync`.
        Runs the blocking Google API calls in the default thread-pool executor.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            partial(self._fetch_new_messages_sync, history_id),
        )

    # ── Send reply ─────────────────────────────────────────────────────────────

    def _send_reply_sync(
        self,
        to_email: str,
        subject: str,
        body: str,
        thread_id: str | None = None,
    ) -> None:
        """
        Build a MIME message and send it via the Gmail API.
        If thread_id is provided the reply lands in the same Gmail thread.
        (Synchronous — runs in thread pool.)
        """
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        mime_msg = MIMEMultipart("alternative")
        mime_msg["To"] = to_email
        mime_msg["Subject"] = (
            subject if subject.lower().startswith("re:") else f"Re: {subject}"
        )

        mime_msg.attach(MIMEText(body, "plain", "utf-8"))

        # Encode to RFC 4648 URL-safe base64 (required by Gmail API)
        raw_bytes = mime_msg.as_bytes()
        encoded = base64.urlsafe_b64encode(raw_bytes).decode("utf-8")

        send_body: dict = {"raw": encoded}
        if thread_id:
            send_body["threadId"] = thread_id

        try:
            self.service.users().messages().send(
                userId="me", body=send_body
            ).execute()
            logger.info(
                "Gmail reply sent: to=%s thread_id=%s", to_email, thread_id
            )
        except HttpError as exc:
            logger.error(
                "Gmail send failed: to=%s thread_id=%s error=%s",
                to_email,
                thread_id,
                exc,
            )
            raise

    async def send_reply(
        self,
        to_email: str,
        subject: str,
        body: str,
        thread_id: str | None = None,
    ) -> None:
        """Async wrapper for _send_reply_sync."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            partial(self._send_reply_sync, to_email, subject, body, thread_id),
        )


# ── Module-level singleton (shared across requests) ────────────────────────────
gmail_service = GmailService()
