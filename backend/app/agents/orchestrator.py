"""
Agent 1: Orchestrator Agent - Master Controller
Coordinates all agents, manages workflow state, monitors progress across all 8 companies,
escalates issues, and sends daily executive summary emails.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.agents.base import BaseAgent
from app.models.company import Company
from app.models.agent import WorkflowRun, AgentTask, AgentLog
from app.models.notification import Notification
from app.services.workflow_engine import WorkflowEngine, WorkflowState

logger = logging.getLogger(__name__)


class OrchestratorAgent(BaseAgent):
    AGENT_TYPE = "orchestrator"
    AGENT_NAME = "Orchestrator Agent"
    DESCRIPTION = "Master controller that coordinates all agents and manages the month-end close workflow"

    def __init__(self, db: Session):
        super().__init__(db)
        self.workflow_engine = WorkflowEngine(db)

    async def execute(self, company_id: Optional[str] = None, period: str = "2026-01", **kwargs) -> Dict[str, Any]:
        """Orchestrate the full month-end close workflow."""
        action = kwargs.get("action", "full_close")

        if action == "full_close":
            return await self._initiate_full_close(period)
        elif action == "health_check":
            return await self._health_check()
        elif action == "daily_summary":
            return await self._generate_daily_summary(period)
        elif action == "monitor_data":
            return await self._monitor_data_changes(period)
        else:
            return await self._initiate_full_close(period)

    async def _initiate_full_close(self, period: str) -> Dict[str, Any]:
        """Start the full month-end close process for all companies."""
        companies = self.db.query(Company).all()
        findings = []
        actions = []

        # Check if a workflow is already running
        active = (
            self.db.query(WorkflowRun)
            .filter_by(status=WorkflowState.RUNNING.value, period=period)
            .first()
        )
        if active:
            findings.append({
                "title": "Active Workflow Detected",
                "description": f"Workflow #{active.id} is already running for period {period}",
                "severity": "info",
            })
            return {
                "status": "completed",
                "workflow_id": active.id,
                "findings": findings,
                "actions": ["Monitoring existing workflow"],
            }

        # Create new workflow
        workflow = self.workflow_engine.create_workflow(
            workflow_type="month_end_close",
            period=period,
            trigger="orchestrator",
        )
        workflow.status = WorkflowState.RUNNING.value
        self.db.commit()

        # Update company statuses
        for company in companies:
            company.close_status = "in_progress"
            company.close_progress = 0.0
            company.close_period = period

        self.db.commit()

        actions.append(f"Created workflow #{workflow.id} with {workflow.total_steps} tasks")
        actions.append(f"Initialized close process for {len(companies)} companies")

        # Use LLM to generate executive briefing
        company_list = ", ".join([c.name for c in companies])
        llm_result = await self.call_llm(
            prompt=f"""Generate a brief executive summary for starting a month-end close process.
Period: {period}
Companies: {company_list}
Total automated tasks: {workflow.total_steps}

Return JSON with keys: summary, risk_areas, estimated_duration_hours, priority_companies""",
            system="You are a senior financial controller AI. Provide concise, actionable summaries."
        )

        return {
            "status": "completed",
            "workflow_id": workflow.id,
            "total_tasks": workflow.total_steps,
            "companies_count": len(companies),
            "findings": findings,
            "actions": actions,
            "llm_briefing": llm_result if isinstance(llm_result, dict) else {"summary": str(llm_result)},
        }

    async def _health_check(self) -> Dict[str, Any]:
        """Check the health of all agents and system components."""
        findings = []

        # Check for stale running tasks (> 30 min)
        stale_tasks = (
            self.db.query(AgentTask)
            .filter_by(status="running")
            .all()
        )
        for task in stale_tasks:
            if task.started_at:
                age = (datetime.utcnow() - task.started_at).total_seconds()
                if age > 1800:  # 30 minutes
                    findings.append({
                        "title": f"Stale Task: {task.agent_type}",
                        "description": f"Task #{task.id} has been running for {int(age/60)} minutes",
                        "severity": "warning",
                        "task_id": task.id,
                    })

        # Check for failed workflows
        failed_workflows = (
            self.db.query(WorkflowRun)
            .filter_by(status="failed")
            .order_by(WorkflowRun.created_at.desc())
            .limit(5)
            .all()
        )
        for wf in failed_workflows:
            findings.append({
                "title": f"Failed Workflow #{wf.id}",
                "description": wf.error_message or "Unknown error",
                "severity": "error",
            })

        # Count recent agent activities
        recent_logs = (
            self.db.query(AgentLog.agent_type, func.count(AgentLog.id))
            .filter(AgentLog.status == "completed")
            .group_by(AgentLog.agent_type)
            .all()
        )
        agent_stats = {agent_type: count for agent_type, count in recent_logs}

        return {
            "status": "completed",
            "system_healthy": len([f for f in findings if f["severity"] == "error"]) == 0,
            "findings": findings,
            "agent_stats": agent_stats,
            "stale_tasks_count": len(stale_tasks),
            "actions": ["Health check completed"],
        }

    async def _generate_daily_summary(self, period: str) -> Dict[str, Any]:
        """Generate daily executive summary for email dispatch."""
        companies = self.db.query(Company).all()

        company_statuses = []
        for c in companies:
            company_statuses.append({
                "name": c.name,
                "status": c.close_status,
                "progress": c.close_progress,
                "industry": c.industry,
            })

        # Count issues by severity
        issue_counts = {}
        for severity in ["info", "warning", "error", "critical"]:
            count = (
                self.db.query(Notification)
                .filter_by(severity=severity, is_read=False)
                .count()
            )
            issue_counts[severity] = count

        # Recent workflow completions
        recent_workflows = (
            self.db.query(WorkflowRun)
            .order_by(WorkflowRun.created_at.desc())
            .limit(5)
            .all()
        )

        # Generate LLM summary
        llm_result = await self.call_llm(
            prompt=f"""Generate an executive daily summary email for month-end close progress.
Period: {period}
Company statuses: {company_statuses}
Open issues: {issue_counts}
Date: {datetime.now().strftime('%B %d, %Y')}

Return JSON with keys: headline, key_highlights (list), attention_items (list), overall_status (on_track/at_risk/behind)""",
            system="You are generating a PE fund executive summary. Be concise, data-driven, and highlight what matters."
        )

        return {
            "status": "completed",
            "findings": [],
            "actions": ["Daily summary generated"],
            "summary": {
                "company_statuses": company_statuses,
                "issue_counts": issue_counts,
                "llm_summary": llm_result if isinstance(llm_result, dict) else {},
            },
        }

    async def _monitor_data_changes(self, period: str) -> Dict[str, Any]:
        """Monitor for new data uploads or changes that should trigger agent work."""
        # Check if there are companies with status not_started
        pending_companies = (
            self.db.query(Company)
            .filter_by(close_status="not_started")
            .all()
        )

        findings = []
        actions = []

        if pending_companies:
            findings.append({
                "title": "Pending Companies Detected",
                "description": f"{len(pending_companies)} companies have not started close process",
                "severity": "warning",
            })
            actions.append("Consider initiating close workflow")

        return {
            "status": "completed",
            "findings": findings,
            "actions": actions,
            "pending_companies": [c.id for c in pending_companies],
        }
