"""
Notification service.

Sends notifications to the support team (email + Slack) and to customers
(satisfaction survey email). All methods are best-effort — failures are
logged as warnings and never propagated to callers.

Delivery transports:
  - Email   : aiosmtplib (same SMTP config used for outbound replies)
  - Slack   : httpx POST to a Slack incoming webhook (Block Kit format)
"""

import email.mime.multipart
import email.mime.text
import logging

import aiosmtplib
import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def send_smtp_email(
    to_email: str,
    subject: str,
    body: str,
    from_email: str | None = None,
) -> bool:
    """
    Send an email via SMTP using aiosmtplib.
    
    This is a shared helper used by both notification_service and response_handler.
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        body: Plain text email body
        from_email: Optional override for sender email
    
    Returns:
        True if sent successfully, False otherwise
    """
    if not settings.smtp_host:
        logger.debug("SMTP not configured — skipping email delivery.")
        return False

    mime_msg = email.mime.multipart.MIMEMultipart("alternative")
    mime_msg["From"] = from_email or settings.smtp_from_email or settings.smtp_user
    mime_msg["To"] = to_email
    mime_msg["Subject"] = subject
    mime_msg.attach(email.mime.text.MIMEText(body, "plain", "utf-8"))

    try:
        await aiosmtplib.send(
            mime_msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            use_tls=settings.smtp_use_tls,
            timeout=15,
        )
        logger.info("SMTP email sent: to=%s subject=%r", to_email, subject)
        return True
    except Exception as exc:
        logger.warning("Failed to send SMTP email to %s: %s", to_email, exc)
        return False


class NotificationService:

    # ── Internal transports ───────────────────────────────────────────────────

    async def _send_email(self, to_email: str, subject: str, body: str) -> None:
        """Send a plain-text email via configured SMTP. Silently skipped if unconfigured."""
        if not to_email:
            logger.debug("No recipient email provided — skipping notification.")
            return

        await send_smtp_email(to_email=to_email, subject=subject, body=body)

    async def _post_slack(self, blocks: list[dict]) -> None:
        """POST a Slack Block Kit payload to the configured incoming webhook."""
        if not settings.slack_webhook_url:
            logger.debug("Slack webhook not configured — skipping Slack notification.")
            return

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    settings.slack_webhook_url,
                    json={"blocks": blocks},
                )
                resp.raise_for_status()
            logger.debug("Slack notification delivered.")
        except Exception as exc:
            logger.warning("Failed to send Slack notification: %s", exc)

    # ── Team notifications ────────────────────────────────────────────────────

    async def notify_escalation(
        self,
        ticket_id: str,
        subject: str,
        customer_name: str,
        customer_email: str,
        reason: str,
        priority: str,
        channel: str,
    ) -> None:
        """Notify the support team when a ticket is escalated."""
        if not settings.support_team_email and not settings.slack_webhook_url:
            return

        email_body = (
            f"A ticket has been escalated and requires human attention.\n\n"
            f"Ticket ID : {ticket_id}\n"
            f"Subject   : {subject}\n"
            f"Customer  : {customer_name} <{customer_email}>\n"
            f"Channel   : {channel}\n"
            f"Priority  : {priority.upper()}\n"
            f"Reason    : {reason}\n\n"
            f"Please review and respond as soon as possible.\n"
            f"{settings.app_base_url}/admin/tickets/{ticket_id}"
        )

        if settings.support_team_email:
            await self._send_email(
                to_email=settings.support_team_email,
                subject=f"[ESCALATED] {subject}",
                body=email_body,
            )

        await self._post_slack(
            [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": ":rotating_light: Ticket Escalated",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Ticket ID:*\n{ticket_id}"},
                        {"type": "mrkdwn", "text": f"*Priority:*\n{priority.upper()}"},
                        {"type": "mrkdwn", "text": f"*Customer:*\n{customer_name}"},
                        {"type": "mrkdwn", "text": f"*Channel:*\n{channel}"},
                    ],
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Subject:* {subject}\n*Reason:* {reason}",
                    },
                },
            ]
        )

    async def notify_sla_breach(
        self,
        ticket_id: str,
        subject: str,
        customer_name: str,
        hours_open: float,
        priority: str,
    ) -> None:
        """Notify the support team when a ticket has breached its SLA."""
        if not settings.support_team_email and not settings.slack_webhook_url:
            return

        email_body = (
            f"A ticket has exceeded its SLA response time and requires immediate action.\n\n"
            f"Ticket ID   : {ticket_id}\n"
            f"Subject     : {subject}\n"
            f"Customer    : {customer_name}\n"
            f"Priority    : {priority.upper()}\n"
            f"Open for    : {hours_open:.1f}h  (SLA: {settings.escalation_sla_hours}h)\n\n"
            f"Please action this ticket immediately.\n"
            f"{settings.app_base_url}/admin/tickets/{ticket_id}"
        )

        if settings.support_team_email:
            await self._send_email(
                to_email=settings.support_team_email,
                subject=f"[SLA BREACH] {subject}",
                body=email_body,
            )

        await self._post_slack(
            [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": ":alarm_clock: SLA Breach",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Ticket ID:*\n{ticket_id}"},
                        {"type": "mrkdwn", "text": f"*Priority:*\n{priority.upper()}"},
                        {
                            "type": "mrkdwn",
                            "text": f"*Open for:*\n{hours_open:.1f}h",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*SLA:*\n{settings.escalation_sla_hours}h",
                        },
                    ],
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Subject:* {subject}\n*Customer:* {customer_name}",
                    },
                },
            ]
        )

    async def notify_ticket_reopened(
        self,
        ticket_id: str,
        subject: str,
        customer_name: str,
        reason: str,
    ) -> None:
        """Notify the support team when a resolved ticket is reopened."""
        if not settings.support_team_email and not settings.slack_webhook_url:
            return

        email_body = (
            f"A resolved ticket has been reopened and requires follow-up.\n\n"
            f"Ticket ID : {ticket_id}\n"
            f"Subject   : {subject}\n"
            f"Customer  : {customer_name}\n"
            f"Reason    : {reason}\n\n"
            f"{settings.app_base_url}/admin/tickets/{ticket_id}"
        )

        if settings.support_team_email:
            await self._send_email(
                to_email=settings.support_team_email,
                subject=f"[REOPENED] {subject}",
                body=email_body,
            )

        await self._post_slack(
            [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": ":arrows_counterclockwise: Ticket Reopened",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Ticket ID:*\n{ticket_id}"},
                        {"type": "mrkdwn", "text": f"*Customer:*\n{customer_name}"},
                    ],
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Subject:* {subject}\n*Reason:* {reason}",
                    },
                },
            ]
        )

    # ── Customer notifications ─────────────────────────────────────────────────

    async def send_satisfaction_survey(
        self,
        to_email: str,
        customer_name: str,
        ticket_id: str,
        subject: str,
    ) -> None:
        """
        Email the customer a post-resolution satisfaction survey.

        The survey link encodes the ticket_id so responses can be routed
        back to the correct ticket by the worker.
        """
        if not to_email:
            return

        survey_url = f"{settings.app_base_url}/survey/{ticket_id}"
        body = (
            f"Hi {customer_name},\n\n"
            f"We recently resolved your support request:\n"
            f"  \"{subject}\"\n\n"
            f"We'd love to hear how we did. Please rate your experience (1–5) by\n"
            f"replying to this email with: Rating: <number>\n\n"
            f"Or click the link below:\n"
            f"  {survey_url}\n\n"
            f"  1 = Very dissatisfied   5 = Very satisfied\n\n"
            f"This survey closes in {settings.survey_response_window_hours} hours.\n\n"
            f"Thank you,\nThe Support Team"
        )
        await self._send_email(
            to_email=to_email,
            subject=f"How did we do? — {subject}",
            body=body,
        )


# ── Module-level singleton ─────────────────────────────────────────────────────

notification_service = NotificationService()
