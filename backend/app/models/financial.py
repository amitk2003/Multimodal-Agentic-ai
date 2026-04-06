"""
Financial data models - Trial Balances, Budgets, Intercompany, Bank Statements, Accruals.
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class TrialBalanceLine(Base):
    __tablename__ = "trial_balance_lines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(String(50), ForeignKey("companies.id"), nullable=False, index=True)
    period = Column(String(10), nullable=False, index=True)  # "2026-01"
    account_code = Column(Integer, nullable=False)
    account_name = Column(String(100), nullable=False)
    debit = Column(Float, default=0.0)
    credit = Column(Float, default=0.0)
    balance = Column(Float, default=0.0)
    account_type = Column(String(30), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="trial_balance_lines")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "company_id": self.company_id,
            "period": self.period,
            "account_code": self.account_code,
            "account_name": self.account_name,
            "debit": self.debit,
            "credit": self.credit,
            "balance": self.balance,
            "account_type": self.account_type,
        }


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(String(50), ForeignKey("companies.id"), nullable=False, index=True)
    company_name = Column(String(100))
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    account_code = Column(Integer, nullable=False)
    account_name = Column(String(100), nullable=False)
    budget_amount = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="budgets")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "company_id": self.company_id,
            "year": self.year,
            "month": self.month,
            "account_code": self.account_code,
            "account_name": self.account_name,
            "budget_amount": self.budget_amount,
        }


class IntercompanyTransaction(Base):
    __tablename__ = "intercompany_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(30), unique=True, nullable=False)
    date = Column(String(10), nullable=False)
    selling_entity_id = Column(String(50), nullable=False, index=True)
    selling_entity_name = Column(String(100))
    buying_entity_id = Column(String(50), nullable=False, index=True)
    buying_entity_name = Column(String(100))
    description = Column(String(200))
    amount = Column(Float, nullable=False)
    gl_account = Column(Integer)
    period = Column(String(10), index=True)
    is_eliminated = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "transaction_id": self.transaction_id,
            "date": self.date,
            "selling_entity_id": self.selling_entity_id,
            "selling_entity_name": self.selling_entity_name,
            "buying_entity_id": self.buying_entity_id,
            "buying_entity_name": self.buying_entity_name,
            "description": self.description,
            "amount": self.amount,
            "gl_account": self.gl_account,
            "is_eliminated": bool(self.is_eliminated),
        }


class BankStatement(Base):
    __tablename__ = "bank_statements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(String(50), ForeignKey("companies.id"), nullable=False, index=True)
    company_name = Column(String(100))
    period = Column(String(10), index=True)
    date = Column(String(10), nullable=False)
    description = Column(String(200))
    debit = Column(Float, nullable=True)
    credit = Column(Float, nullable=True)
    balance = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="bank_statements")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "company_id": self.company_id,
            "date": self.date,
            "description": self.description,
            "debit": self.debit,
            "credit": self.credit,
            "balance": self.balance,
        }


class AccrualSchedule(Base):
    __tablename__ = "accrual_schedules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(String(50), ForeignKey("companies.id"), nullable=False, index=True)
    company_name = Column(String(100))
    accrual_type = Column(String(200), nullable=False)
    gl_account = Column(Integer, nullable=False)
    frequency = Column(String(20), nullable=False)
    amount = Column(Float, nullable=False)
    last_booked_date = Column(String(10))
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="accrual_schedules")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "company_id": self.company_id,
            "accrual_type": self.accrual_type,
            "gl_account": self.gl_account,
            "frequency": self.frequency,
            "amount": self.amount,
            "last_booked_date": self.last_booked_date,
        }
