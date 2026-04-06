"""
Agent and Workflow models - tracking agent activity, workflow state, and task execution.
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class AgentLog(Base):
    """Tracks every action taken by every agent - the audit trail."""
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_type = Column(String(50), nullable=False, index=True)
    company_id = Column(String(50), ForeignKey("companies.id"), nullable=True, index=True)
    workflow_run_id = Column(Integer, ForeignKey("workflow_runs.id"), nullable=True)
    action = Column(String(200), nullable=False)
    status = Column(String(20), nullable=False, default="running")  # running, completed, failed, warning
    severity = Column(String(20), default="info")  # info, warning, error, critical
    details = Column(JSON, nullable=True)
    reasoning = Column(Text, nullable=True)  # LLM reasoning trace
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    company = relationship("Company", back_populates="agent_logs")
    workflow_run = relationship("WorkflowRun", back_populates="agent_logs")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "agent_type": self.agent_type,
            "company_id": self.company_id,
            "workflow_run_id": self.workflow_run_id,
            "action": self.action,
            "status": self.status,
            "severity": self.severity,
            "details": self.details,
            "reasoning": self.reasoning,
            "duration_ms": self.duration_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class WorkflowRun(Base):
    """Tracks end-to-end workflow execution for a close cycle."""
    __tablename__ = "workflow_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_type = Column(String(50), nullable=False)  # month_end_close, daily_check, etc.
    status = Column(String(20), nullable=False, default="pending")  # pending, running, completed, failed
    period = Column(String(10), nullable=True)  # "2026-01"
    trigger = Column(String(30), default="scheduled")  # scheduled, manual, event
    total_steps = Column(Integer, default=0)
    completed_steps = Column(Integer, default=0)
    progress = Column(Float, default=0.0)
    metadata_ = Column("metadata", JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    agent_logs = relationship("AgentLog", back_populates="workflow_run")
    tasks = relationship("AgentTask", back_populates="workflow_run")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workflow_type": self.workflow_type,
            "status": self.status,
            "period": self.period,
            "trigger": self.trigger,
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "progress": self.progress,
            "metadata": self.metadata_,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AgentTask(Base):
    """Individual task within a workflow - one agent + one company."""
    __tablename__ = "agent_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_run_id = Column(Integer, ForeignKey("workflow_runs.id"), nullable=False)
    agent_type = Column(String(50), nullable=False)
    company_id = Column(String(50), nullable=True)
    status = Column(String(20), default="pending")  # pending, running, completed, failed, skipped
    priority = Column(Integer, default=5)  # 1=highest, 10=lowest
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    workflow_run = relationship("WorkflowRun", back_populates="tasks")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workflow_run_id": self.workflow_run_id,
            "agent_type": self.agent_type,
            "company_id": self.company_id,
            "status": self.status,
            "priority": self.priority,
            "result": self.result,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
