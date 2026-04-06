"""
Data Loader Service - Loads CSV/JSON sample data into PostgreSQL.
Handles all 8 portfolio companies, trial balances, budgets, intercompany transactions,
bank statements, and accrual schedules.
"""
import pandas as pd
import json
import os
import logging
from pathlib import Path
from sqlalchemy.orm import Session
from typing import Optional

from app.models.company import Company
from app.models.financial import (
    TrialBalanceLine, Budget, IntercompanyTransaction,
    BankStatement, AccrualSchedule
)
from app.models.agent import AgentLog, WorkflowRun, AgentTask
from app.models.notification import Notification, Report
from app.config import settings

logger = logging.getLogger(__name__)


class DataLoader:
    """Loads assignment sample data from CSV/JSON files into the database."""

    def __init__(self, db: Session, data_dir: Optional[str] = None):
        self.db = db
        self.data_dir = Path(data_dir or settings.DATA_DIR)

    def load_all(self) -> dict:
        """Load all data files into the database. Returns summary stats."""
        stats = {}
        logger.info(f"Loading data from {self.data_dir}")

        stats["companies"] = self._load_companies()
        stats["trial_balances"] = self._load_trial_balances()
        stats["prior_year"] = self._load_prior_year()
        stats["budgets"] = self._load_budgets()
        stats["intercompany"] = self._load_intercompany()
        stats["bank_statements"] = self._load_bank_statements()
        stats["accrual_schedules"] = self._load_accrual_schedules()

        self.db.commit()
        logger.info(f"Data loading complete: {stats}")
        return stats

    def _load_companies(self) -> int:
        """Load company metadata from JSON."""
        metadata_path = self.data_dir / "company_metadata.json"
        if not metadata_path.exists():
            logger.warning(f"Company metadata not found at {metadata_path}")
            return 0

        with open(metadata_path, "r") as f:
            companies = json.load(f)

        count = 0
        for c in companies:
            existing = self.db.query(Company).filter_by(id=c["id"]).first()
            if not existing:
                company = Company(
                    id=c["id"],
                    name=c["name"],
                    industry=c["industry"],
                    revenue_annual=c["revenue_annual"],
                    employees=c["employees"],
                    has_inventory=c["has_inventory"],
                    gross_margin=c["gross_margin"],
                    growth_rate=c["growth_rate"],
                    close_status="not_started",
                    close_progress=0.0,
                )
                self.db.add(company)
                count += 1

        self.db.flush()
        logger.info(f"Loaded {count} companies")
        return count

    def _load_trial_balances(self) -> int:
        """Load trial balance CSV files for all companies and periods."""
        tb_dir = self.data_dir / "trial_balances"
        if not tb_dir.exists():
            return 0

        count = 0
        for csv_file in sorted(tb_dir.glob("*.csv")):
            df = pd.read_csv(csv_file)
            for _, row in df.iterrows():
                tb = TrialBalanceLine(
                    company_id=row.get("company_id", ""),
                    period=row.get("period", ""),
                    account_code=int(row.get("account_code", 0)),
                    account_name=str(row.get("account_name", "")),
                    debit=float(row.get("debit", 0) or 0),
                    credit=float(row.get("credit", 0) or 0),
                    balance=float(row.get("balance", 0) or 0),
                    account_type=str(row.get("account_type", "")),
                )
                self.db.add(tb)
                count += 1

        self.db.flush()
        logger.info(f"Loaded {count} trial balance lines")
        return count

    def _load_prior_year(self) -> int:
        """Load prior year trial balance data the same way."""
        py_dir = self.data_dir / "prior_year"
        if not py_dir.exists():
            return 0

        count = 0
        for csv_file in sorted(py_dir.glob("*.csv")):
            df = pd.read_csv(csv_file)
            for _, row in df.iterrows():
                tb = TrialBalanceLine(
                    company_id=row.get("company_id", ""),
                    period=row.get("period", ""),
                    account_code=int(row.get("account_code", 0)),
                    account_name=str(row.get("account_name", "")),
                    debit=float(row.get("debit", 0) or 0),
                    credit=float(row.get("credit", 0) or 0),
                    balance=float(row.get("balance", 0) or 0),
                    account_type=str(row.get("account_type", "")),
                )
                self.db.add(tb)
                count += 1

        self.db.flush()
        logger.info(f"Loaded {count} prior year lines")
        return count

    def _load_budgets(self) -> int:
        """Load budget data."""
        budget_dir = self.data_dir / "budgets"
        if not budget_dir.exists():
            return 0

        count = 0
        for csv_file in budget_dir.glob("*.csv"):
            df = pd.read_csv(csv_file)
            for _, row in df.iterrows():
                budget = Budget(
                    company_id=row.get("company_id", ""),
                    company_name=row.get("company_name", ""),
                    year=int(row.get("year", 2026)),
                    month=int(row.get("month", 1)),
                    account_code=int(row.get("account_code", 0)),
                    account_name=str(row.get("account_name", "")),
                    budget_amount=float(row.get("budget_amount", 0) or 0),
                )
                self.db.add(budget)
                count += 1

        self.db.flush()
        logger.info(f"Loaded {count} budget records")
        return count

    def _load_intercompany(self) -> int:
        """Load intercompany transaction data."""
        ic_dir = self.data_dir / "intercompany"
        if not ic_dir.exists():
            return 0

        count = 0
        for csv_file in sorted(ic_dir.glob("*.csv")):
            df = pd.read_csv(csv_file)
            # Extract period from filename
            period = csv_file.stem.replace("intercompany_", "").replace("_", "-")

            for _, row in df.iterrows():
                ic = IntercompanyTransaction(
                    transaction_id=str(row.get("transaction_id", "")),
                    date=str(row.get("date", "")),
                    selling_entity_id=str(row.get("selling_entity_id", "")),
                    selling_entity_name=str(row.get("selling_entity_name", "")),
                    buying_entity_id=str(row.get("buying_entity_id", "")),
                    buying_entity_name=str(row.get("buying_entity_name", "")),
                    description=str(row.get("description", "")),
                    amount=float(row.get("amount", 0) or 0),
                    gl_account=int(row.get("gl_account", 0)) if pd.notna(row.get("gl_account")) else None,
                    period=period,
                )
                self.db.add(ic)
                count += 1

        self.db.flush()
        logger.info(f"Loaded {count} intercompany transactions")
        return count

    def _load_bank_statements(self) -> int:
        """Load bank statement data."""
        bs_dir = self.data_dir / "bank_statements"
        if not bs_dir.exists():
            return 0

        count = 0
        for csv_file in sorted(bs_dir.glob("*.csv")):
            df = pd.read_csv(csv_file)
            for _, row in df.iterrows():
                bs = BankStatement(
                    company_id=str(row.get("company_id", "")),
                    company_name=str(row.get("company_name", "")),
                    period=str(row.get("period", "")),
                    date=str(row.get("date", "")),
                    description=str(row.get("description", "")),
                    debit=float(row["debit"]) if pd.notna(row.get("debit")) else None,
                    credit=float(row["credit"]) if pd.notna(row.get("credit")) else None,
                    balance=float(row.get("balance", 0) or 0),
                )
                self.db.add(bs)
                count += 1

        self.db.flush()
        logger.info(f"Loaded {count} bank statement lines")
        return count

    def _load_accrual_schedules(self) -> int:
        """Load accrual schedule data."""
        accrual_dir = self.data_dir / "accrual_schedules"
        if not accrual_dir.exists():
            return 0

        count = 0
        for csv_file in accrual_dir.glob("*.csv"):
            df = pd.read_csv(csv_file)
            for _, row in df.iterrows():
                accrual = AccrualSchedule(
                    company_id=str(row.get("company_id", "")),
                    company_name=str(row.get("company_name", "")),
                    accrual_type=str(row.get("accrual_type", "")),
                    gl_account=int(row.get("gl_account", 0)),
                    frequency=str(row.get("frequency", "")),
                    amount=float(row.get("amount", 0) or 0),
                    last_booked_date=str(row.get("last_booked_date", "")),
                )
                self.db.add(accrual)
                count += 1

        self.db.flush()
        logger.info(f"Loaded {count} accrual schedules")
        return count

    def clear_all(self):
        """Clear all data from database tables (for re-seeding)."""
        self.db.query(Report).delete()
        self.db.query(Notification).delete()
        self.db.query(AgentLog).delete()
        self.db.query(AgentTask).delete()
        self.db.query(WorkflowRun).delete()
        self.db.query(AccrualSchedule).delete()
        self.db.query(BankStatement).delete()
        self.db.query(IntercompanyTransaction).delete()
        self.db.query(Budget).delete()
        self.db.query(TrialBalanceLine).delete()
        self.db.query(Company).delete()
        self.db.commit()
        logger.info("All data cleared")
