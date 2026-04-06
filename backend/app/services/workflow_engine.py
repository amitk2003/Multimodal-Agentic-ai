"""
Workflow Engine - State machine for managing month-end close workflows.
Handles the orchestration flow: parallel groups, sequential dependencies,
event emission, and progress tracking.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from sqlalchemy.orm import Session

from app.models.agent import WorkflowRun, AgentTask
from app.models.company import Company

logger = logging.getLogger(__name__)


class WorkflowState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class ExecutionGroup:
    """Defines a group of agent tasks that execute together."""

    def __init__(self, name: str, agent_types: List[str], parallel: bool = True, per_company: bool = True):
        self.name = name
        self.agent_types = agent_types
        self.parallel = parallel
        self.per_company = per_company


# Define the month-end close workflow execution groups
CLOSE_WORKFLOW_GROUPS = [
    ExecutionGroup(
        name="Validation & Analysis",
        agent_types=["trial_balance_validator", "variance_analysis", "cash_flow_reconciliation"],
        parallel=True,
        per_company=True,
    ),
    ExecutionGroup(
        name="Verification",
        agent_types=["accrual_verification", "revenue_recognition", "expense_categorization"],
        parallel=False,
        per_company=True,
    ),
    ExecutionGroup(
        name="Cross-Company",
        agent_types=["intercompany_elimination"],
        parallel=False,
        per_company=False,
    ),
    ExecutionGroup(
        name="Consolidation & Reporting",
        agent_types=["consolidation", "reporting_communication"],
        parallel=False,
        per_company=False,
    ),
]


class WorkflowEngine:
    """Manages workflow state transitions and task scheduling."""

    def __init__(self, db: Session):
        self.db = db

    def create_workflow(self, workflow_type: str, period: str, trigger: str = "scheduled") -> WorkflowRun:
        """Create a new workflow run with all required tasks."""
        companies = self.db.query(Company).all()

        # Calculate total steps
        total_steps = 0
        for group in CLOSE_WORKFLOW_GROUPS:
            if group.per_company:
                total_steps += len(group.agent_types) * len(companies)
            else:
                total_steps += len(group.agent_types)

        workflow = WorkflowRun(
            workflow_type=workflow_type,
            status=WorkflowState.PENDING.value,
            period=period,
            trigger=trigger,
            total_steps=total_steps,
            completed_steps=0,
            progress=0.0,
            started_at=datetime.utcnow(),
        )
        self.db.add(workflow)
        self.db.flush()

        # Create individual tasks
        priority = 1
        for group in CLOSE_WORKFLOW_GROUPS:
            for agent_type in group.agent_types:
                if group.per_company:
                    for company in companies:
                        task = AgentTask(
                            workflow_run_id=workflow.id,
                            agent_type=agent_type,
                            company_id=company.id,
                            status="pending",
                            priority=priority,
                        )
                        self.db.add(task)
                else:
                    task = AgentTask(
                        workflow_run_id=workflow.id,
                        agent_type=agent_type,
                        company_id=None,
                        status="pending",
                        priority=priority,
                    )
                    self.db.add(task)
            priority += 1

        self.db.commit()
        logger.info(f"Created workflow {workflow.id} with {total_steps} tasks")
        return workflow

    def get_next_tasks(self, workflow_id: int) -> List[AgentTask]:
        """Get the next batch of tasks to execute based on group dependencies."""
        workflow = self.db.query(WorkflowRun).get(workflow_id)
        if not workflow or workflow.status != WorkflowState.RUNNING.value:
            return []

        # Find highest priority group with pending tasks
        pending_tasks = (
            self.db.query(AgentTask)
            .filter_by(workflow_run_id=workflow_id, status="pending")
            .order_by(AgentTask.priority)
            .all()
        )

        if not pending_tasks:
            return []

        # Get all tasks at the same priority level
        min_priority = pending_tasks[0].priority
        return [t for t in pending_tasks if t.priority == min_priority]

    def complete_task(self, task_id: int, result: Optional[Dict] = None, error: Optional[str] = None):
        """Mark a task as completed or failed and update workflow progress."""
        task = self.db.query(AgentTask).get(task_id)
        if not task:
            return

        if error:
            task.status = "failed"
            task.error_message = error
        else:
            task.status = "completed"
            task.result = result

        task.completed_at = datetime.utcnow()

        # Update workflow progress
        workflow = self.db.query(WorkflowRun).get(task.workflow_run_id)
        if workflow:
            completed = (
                self.db.query(AgentTask)
                .filter_by(workflow_run_id=workflow.id)
                .filter(AgentTask.status.in_(["completed", "failed", "skipped"]))
                .count()
            )
            workflow.completed_steps = completed
            workflow.progress = (completed / workflow.total_steps * 100) if workflow.total_steps > 0 else 0

            # Check if all tasks in current group are done
            pending = (
                self.db.query(AgentTask)
                .filter_by(workflow_run_id=workflow.id, status="pending")
                .count()
            )
            running = (
                self.db.query(AgentTask)
                .filter_by(workflow_run_id=workflow.id, status="running")
                .count()
            )

            if pending == 0 and running == 0:
                workflow.status = WorkflowState.COMPLETED.value
                workflow.completed_at = datetime.utcnow()

        self.db.commit()

    def fail_workflow(self, workflow_id: int, error_message: str):
        """Mark an entire workflow as failed."""
        workflow = self.db.query(WorkflowRun).get(workflow_id)
        if workflow:
            workflow.status = WorkflowState.FAILED.value
            workflow.error_message = error_message
            workflow.completed_at = datetime.utcnow()
            self.db.commit()

    def get_workflow_status(self, workflow_id: int) -> Optional[Dict]:
        """Get detailed workflow status including all task statuses."""
        workflow = self.db.query(WorkflowRun).get(workflow_id)
        if not workflow:
            return None

        tasks = self.db.query(AgentTask).filter_by(workflow_run_id=workflow_id).all()
        return {
            **workflow.to_dict(),
            "tasks": [t.to_dict() for t in tasks],
        }
