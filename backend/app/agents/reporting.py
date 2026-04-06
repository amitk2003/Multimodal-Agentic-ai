"""
Agent 10: Reporting & Communication Agent
Generates executive dashboards, variance reports, KPI scorecards,
sends automated email updates, prepares board-ready materials.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.agents.base import BaseAgent
from app.models.company import Company
from app.models.agent import AgentLog, WorkflowRun
from app.models.notification import Notification, Report
from app.models.financial import TrialBalanceLine
from app.services.email_service import email_service

logger = logging.getLogger(__name__)


class ReportingCommunicationAgent(BaseAgent):
    AGENT_TYPE = "reporting_communication"
    AGENT_NAME = "Reporting & Communication Agent"
    DESCRIPTION = "Generates reports, dashboards, and sends stakeholder communications"

    async def execute(self, company_id: Optional[str] = None, period: str = "2026-01", **kwargs) -> Dict[str, Any]:
        findings = []
        actions = []
        report_type = kwargs.get("report_type", "full")

        if report_type == "daily_email":
            return await self._send_daily_summary(period)
        elif report_type == "completion_email":
            return await self._send_completion_report(period)
        elif report_type == "issue_alert":
            return await self._send_issue_alerts(period)
        else:
            return await self._generate_full_report(period)

    async def _generate_full_report(self, period: str) -> Dict[str, Any]:
        """Generate comprehensive monthly report package."""
        actions = []
        findings = []
        companies = self.db.query(Company).all()

        # Gather data from all agent results via shared memory
        consolidation_data = self.memory.get(f"agent:consolidation:all:{period}")
        variance_data = {}
        for company in companies:
            vd = self.memory.get(f"agent:variance_analysis:{company.id}:{period}")
            if vd:
                variance_data[company.id] = vd

        # Portfolio-level KPIs
        total_revenue = 0
        total_ebitda = 0
        company_summaries = []

        for company in companies:
            tb = (
                self.db.query(TrialBalanceLine)
                .filter_by(company_id=company.id, period=period)
                .all()
            )
            rev = sum(abs(l.credit or 0) for l in tb if l.account_type == "Revenue")
            cogs = sum(abs(l.debit or 0) for l in tb if l.account_type == "COGS")
            opex = sum(abs(l.debit or 0) for l in tb if l.account_type == "Operating Expense")
            ebitda = rev - cogs - opex

            total_revenue += rev
            total_ebitda += ebitda

            # Count issues
            issue_count = (
                self.db.query(Notification)
                .filter_by(company_id=company.id)
                .filter(Notification.severity.in_(["warning", "error", "critical"]))
                .count()
            )

            company_summaries.append({
                "company_id": company.id,
                "company_name": company.name,
                "industry": company.industry,
                "revenue": round(rev, 2),
                "ebitda": round(ebitda, 2),
                "margin": round((ebitda / rev * 100) if rev > 0 else 0, 1),
                "close_status": company.close_status,
                "close_progress": company.close_progress,
                "open_issues": issue_count,
            })

        # Count total findings across all agents
        total_findings = self.db.query(Notification).filter(
            Notification.severity.in_(["warning", "error", "critical"])
        ).count()

        # Generate executive summary via LLM
        llm_result = await self.call_llm(
            prompt=f"""Generate a PE fund executive report for period {period}:

Portfolio Overview:
- Total Revenue: ${total_revenue:,.0f}
- Total EBITDA: ${total_ebitda:,.0f}
- Companies: {len(companies)}
- Total Open Issues: {total_findings}

Company Details:
{company_summaries}

Create a professional executive summary suitable for PE partners.

Return JSON:
- executive_headline (1 sentence)
- portfolio_performance (paragraph)
- top_performers (list of company names with reason)
- areas_requiring_attention (list with company, issue, recommendation)
- key_metrics_table (list of dicts with metric, value, trend)
- outlook (paragraph)""",
            system="You are the CFO of a PE firm preparing a board report. Be concise, data-driven, and action-oriented."
        )

        # Save report to database
        report = Report(
            report_type="monthly_executive",
            title=f"Monthly Executive Report - {period}",
            period=period,
            content={
                "company_summaries": company_summaries,
                "total_revenue": total_revenue,
                "total_ebitda": total_ebitda,
                "total_issues": total_findings,
                "llm_analysis": llm_result if isinstance(llm_result, dict) else {},
            },
            generated_by=self.AGENT_TYPE,
        )
        self.db.add(report)
        self.db.commit()

        actions.append(f"Generated executive report for {len(companies)} companies")
        actions.append(f"Portfolio revenue: ${total_revenue:,.0f}, EBITDA: ${total_ebitda:,.0f}")

        return {
            "status": "completed",
            "findings": findings,
            "actions": actions,
            "report": {
                "company_summaries": company_summaries,
                "total_revenue": round(total_revenue, 2),
                "total_ebitda": round(total_ebitda, 2),
                "total_issues": total_findings,
            },
            "llm_analysis": llm_result if isinstance(llm_result, dict) else {},
        }

    async def _send_daily_summary(self, period: str) -> Dict[str, Any]:
        """Send daily executive summary email."""
        companies = self.db.query(Company).all()

        summary_data = {
            "companies": [
                {"name": c.name, "status": c.close_status, "progress": c.close_progress}
                for c in companies
            ],
            "total_companies": len(companies),
            "completed": len([c for c in companies if c.close_status == "completed"]),
            "in_progress": len([c for c in companies if c.close_status == "in_progress"]),
            "period": period,
        }

        success = await email_service.send_daily_summary(summary_data)

        return {
            "status": "completed",
            "findings": [],
            "actions": [f"Daily summary email {'sent' if success else 'prepared (preview mode)'}"],
            "email_sent": success,
        }

    async def _send_completion_report(self, period: str) -> Dict[str, Any]:
        """Send close completion email."""
        results = {
            "period": period,
            "completed_at": datetime.utcnow().isoformat(),
            "companies_processed": self.db.query(Company).count(),
        }

        success = await email_service.send_completion_report(period, results)

        return {
            "status": "completed",
            "findings": [],
            "actions": [f"Completion report email {'sent' if success else 'prepared (preview mode)'}"],
            "email_sent": success,
        }

    async def _send_issue_alerts(self, period: str) -> Dict[str, Any]:
        """Send email alerts for unread critical notifications."""
        critical_notifications = (
            self.db.query(Notification)
            .filter_by(is_emailed=False)
            .filter(Notification.severity.in_(["error", "critical"]))
            .all()
        )

        sent_count = 0
        for notif in critical_notifications:
            success = await email_service.send_issue_alert(
                company_name=notif.company_id or "Portfolio",
                issue_type=notif.notification_type,
                description=notif.message,
                severity=notif.severity,
                details=notif.details,
            )
            if success:
                notif.is_emailed = True
                sent_count += 1

        self.db.commit()

        return {
            "status": "completed",
            "findings": [],
            "actions": [f"Sent {sent_count} issue alert emails"],
            "alerts_sent": sent_count,
        }
