"""
Email Service - Sends automated emails via Resend API.
Handles all email types: daily summaries, issue alerts, completion notices, stakeholder reports.
Uses Jinja2 templates for professional email rendering.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

# Initialize Jinja2 template engine
template_dir = Path(__file__).parent.parent / "templates" / "email"
jinja_env = Environment(
    loader=FileSystemLoader(str(template_dir)),
    autoescape=select_autoescape(["html"]),
)


class EmailService:
    """Handles all automated email dispatch for the platform."""

    def __init__(self):
        self.enabled = settings.EMAIL_ENABLED
        self.from_email = settings.EMAIL_FROM
        self._resend = None

        if self.enabled and settings.RESEND_API_KEY:
            try:
                import resend
                resend.api_key = settings.RESEND_API_KEY
                self._resend = resend
                logger.info("Email service initialized with Resend")
            except ImportError:
                logger.warning("Resend package not installed, emails disabled")
                self.enabled = False

    async def send_daily_summary(self, summary_data: Dict[str, Any]) -> bool:
        """Send daily executive summary email to PE partners."""
        template = jinja_env.get_template("daily_summary.html")
        html_content = template.render(
            date=datetime.now().strftime("%B %d, %Y"),
            **summary_data,
        )

        recipients = [settings.PE_PARTNER_EMAIL]
        return await self._send_email(
            to=recipients,
            subject=f"[Apex Capital] Daily Close Summary - {datetime.now().strftime('%m/%d/%Y')}",
            html=html_content,
        )

    async def send_issue_alert(
        self,
        company_name: str,
        issue_type: str,
        description: str,
        severity: str,
        details: Optional[Dict] = None,
    ) -> bool:
        """Send immediate alert when a critical issue is found by an agent."""
        template = jinja_env.get_template("issue_alert.html")
        html_content = template.render(
            company_name=company_name,
            issue_type=issue_type,
            description=description,
            severity=severity,
            details=details or {},
            timestamp=datetime.now().strftime("%B %d, %Y %I:%M %p"),
        )

        recipients = [settings.PE_PARTNER_EMAIL]
        return await self._send_email(
            to=recipients,
            subject=f"[ALERT] {severity.upper()}: {issue_type} at {company_name}",
            html=html_content,
        )

    async def send_completion_report(
        self,
        period: str,
        results: Dict[str, Any],
    ) -> bool:
        """Send completion notice when close process finishes."""
        template = jinja_env.get_template("completion_report.html")
        html_content = template.render(
            period=period,
            results=results,
            timestamp=datetime.now().strftime("%B %d, %Y %I:%M %p"),
        )

        recipients = [settings.PE_PARTNER_EMAIL] + settings.CFO_EMAILS.split(",")
        return await self._send_email(
            to=recipients,
            subject=f"[Apex Capital] Month-End Close Complete - {period}",
            html=html_content,
        )

    async def send_status_update(
        self,
        recipient: str,
        subject: str,
        content: Dict[str, Any],
    ) -> bool:
        """Send a general status update email."""
        template = jinja_env.get_template("status_update.html")
        html_content = template.render(
            **content,
            timestamp=datetime.now().strftime("%B %d, %Y %I:%M %p"),
        )

        return await self._send_email(
            to=[recipient],
            subject=subject,
            html=html_content,
        )

    async def _send_email(
        self,
        to: List[str],
        subject: str,
        html: str,
    ) -> bool:
        """Internal method to send an email via Resend."""
        if not self.enabled:
            logger.info(f"[EMAIL PREVIEW] To: {to}, Subject: {subject}")
            logger.debug(f"[EMAIL BODY] {html[:500]}...")
            return True  # Return True in preview/test mode

        try:
            params = {
                "from": self.from_email,
                "to": to,
                "subject": subject,
                "html": html,
            }
            response = self._resend.Emails.send(params)
            logger.info(f"Email sent successfully: {subject} -> {to}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False


# Singleton instance
email_service = EmailService()
