"""
Agents API - Endpoints for agent management, activity logs, and workflow control.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.agent import AgentLog, WorkflowRun, AgentTask
from app.models.company import Company

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("/logs")
def get_agent_logs(
    limit: int = 50,
    offset: int = 0,
    agent_type: Optional[str] = None,
    company_id: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get agent activity logs with filtering."""
    query = db.query(AgentLog).order_by(desc(AgentLog.created_at))

    if agent_type:
        query = query.filter_by(agent_type=agent_type)
    if company_id:
        query = query.filter_by(company_id=company_id)
    if severity:
        query = query.filter_by(severity=severity)

    total = query.count()
    logs = query.offset(offset).limit(limit).all()

    return {
        "logs": [log.to_dict() for log in logs],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/status")
def get_agent_status(db: Session = Depends(get_db)):
    """Get current status of all agent types."""
    agent_types = [
        "orchestrator", "trial_balance_validator", "variance_analysis",
        "accrual_verification", "intercompany_elimination", "revenue_recognition",
        "expense_categorization", "cash_flow_reconciliation", "consolidation",
        "reporting_communication",
    ]

    statuses = []
    for agent_type in agent_types:
        # Get latest log for this agent
        latest = (
            db.query(AgentLog)
            .filter_by(agent_type=agent_type)
            .order_by(desc(AgentLog.created_at))
            .first()
        )

        # Count completed tasks
        completed = db.query(AgentLog).filter_by(agent_type=agent_type, status="completed").count()
        failed = db.query(AgentLog).filter_by(agent_type=agent_type, status="failed").count()
        running = db.query(AgentLog).filter_by(agent_type=agent_type, status="running").count()

        statuses.append({
            "agent_type": agent_type,
            "display_name": agent_type.replace("_", " ").title(),
            "status": latest.status if latest else "idle",
            "last_action": latest.action if latest else None,
            "last_run": latest.created_at.isoformat() if latest and latest.created_at else None,
            "completed_count": completed,
            "failed_count": failed,
            "running_count": running,
        })

    return {"agents": statuses}


@router.get("/workflows")
def get_workflows(limit: int = 10, db: Session = Depends(get_db)):
    """Get recent workflow runs."""
    workflows = (
        db.query(WorkflowRun)
        .order_by(desc(WorkflowRun.created_at))
        .limit(limit)
        .all()
    )
    return {"workflows": [w.to_dict() for w in workflows]}


@router.get("/workflows/{workflow_id}")
def get_workflow_detail(workflow_id: int, db: Session = Depends(get_db)):
    """Get detailed workflow status including all tasks."""
    workflow = db.query(WorkflowRun).get(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    tasks = db.query(AgentTask).filter_by(workflow_run_id=workflow_id).order_by(AgentTask.priority).all()

    return {
        **workflow.to_dict(),
        "tasks": [t.to_dict() for t in tasks],
    }


@router.post("/run/{agent_type}")
async def trigger_agent(
    agent_type: str,
    company_id: Optional[str] = None,
    period: str = "2026-01",
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
):
    """Manually trigger an agent run (for testing/demo purposes)."""
    from app.services.scheduler import run_single_agent
    await run_single_agent(agent_type, company_id, period, db)
    return {"message": f"Agent {agent_type} triggered", "company_id": company_id, "period": period}


@router.post("/run-all")
async def trigger_full_close(
    period: str = "2026-01",
    db: Session = Depends(get_db),
):
    """Trigger a full month-end close workflow."""
    from app.services.scheduler import run_full_close
    result = await run_full_close(period, db)
    return {"message": "Full close workflow initiated", "result": result}
