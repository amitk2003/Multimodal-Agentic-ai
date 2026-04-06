"""
Company model - represents portfolio companies managed by Apex Capital Partners.
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class CloseStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    ERROR = "error"


class Company(Base):
    __tablename__ = "companies"

    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    industry = Column(String(50), nullable=False)
    revenue_annual = Column(Float, nullable=False)
    employees = Column(Integer, nullable=False)
    has_inventory = Column(Boolean, default=False)
    gross_margin = Column(Float, nullable=False)
    growth_rate = Column(Float, nullable=False)

    # Close status tracking
    close_status = Column(String(20), default=CloseStatus.NOT_STARTED.value)
    close_progress = Column(Float, default=0.0)
    close_period = Column(String(10), nullable=True)  # e.g., "2026-01"

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    trial_balance_lines = relationship("TrialBalanceLine", back_populates="company", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="company", cascade="all, delete-orphan")
    bank_statements = relationship("BankStatement", back_populates="company", cascade="all, delete-orphan")
    accrual_schedules = relationship("AccrualSchedule", back_populates="company", cascade="all, delete-orphan")
    agent_logs = relationship("AgentLog", back_populates="company", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="company", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "industry": self.industry,
            "revenue_annual": self.revenue_annual,
            "employees": self.employees,
            "has_inventory": self.has_inventory,
            "gross_margin": self.gross_margin,
            "growth_rate": self.growth_rate,
            "close_status": self.close_status,
            "close_progress": self.close_progress,
            "close_period": self.close_period,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
