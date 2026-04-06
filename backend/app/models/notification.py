"""
Notification and Report models for email alerts and generated reports.
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Notification(Base):
    """Notifications for in-app alerts and email dispatch tracking."""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(String(50), ForeignKey("companies.id"), nullable=True)
    notification_type = Column(String(50), nullable=False)  # issue_alert, daily_summary, completion, insight
    severity = Column(String(20), default="info")
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    is_read = Column(Boolean, default=False)
    is_emailed = Column(Boolean, default=False)
    email_to = Column(String(200), nullable=True)
    agent_type = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    company = relationship("Company", back_populates="notifications")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "company_id": self.company_id,
            "notification_type": self.notification_type,
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "details": self.details,
            "is_read": self.is_read,
            "is_emailed": self.is_emailed,
            "agent_type": self.agent_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Report(Base):
    """Generated reports metadata and storage."""
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_type = Column(String(50), nullable=False)  # variance, consolidation, intercompany, executive
    title = Column(String(200), nullable=False)
    period = Column(String(10), nullable=True)
    company_id = Column(String(50), nullable=True)
    format = Column(String(10), default="pdf")  # pdf, csv, xlsx
    file_path = Column(String(500), nullable=True)
    content = Column(JSON, nullable=True)  # Structured report data
    generated_by = Column(String(50), default="system")
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "report_type": self.report_type,
            "title": self.title,
            "period": self.period,
            "company_id": self.company_id,
            "format": self.format,
            "generated_by": self.generated_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
