"""
Scheduler Service - Runs agents autonomously via schedules and event triggers.
"""
import logging
import asyncio
from typing import Optional
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.agents.orchestrator import OrchestratorAgent
from app.agents.trial_balance import TrialBalanceValidatorAgent
from app.agents.variance import VarianceAnalysisAgent
from app.agents.accrual import AccrualVerificationAgent
from app.agents.intercompany import IntercompanyEliminationAgent
from app.agents.revenue_recognition import RevenueRecognitionAgent
from app.agents.expense import ExpenseCategorizationAgent
from app.agents.cash_flow import CashFlowReconciliationAgent
from app.agents.consolidation import ConsolidationAgent
from app.agents.reporting import ReportingCommunicationAgent
from app.models.company import Company

logger = logging.getLogger(__name__)

# Agent registry
AGENT_REGISTRY = {
    "orchestrator": OrchestratorAgent,
    "trial_balance_validator": TrialBalanceValidatorAgent,
    "variance_analysis": VarianceAnalysisAgent,
    "accrual_verification": AccrualVerificationAgent,
    "intercompany_elimination": IntercompanyEliminationAgent,
    "revenue_recognition": RevenueRecognitionAgent,
    "expense_categorization": ExpenseCategorizationAgent,
    "cash_flow_reconciliation": CashFlowReconciliationAgent,
    "consolidation": ConsolidationAgent,
    "reporting_communication": ReportingCommunicationAgent,
}


async def run_single_agent(agent_type: str, company_id: Optional[str], period: str, db: Session):
    """Run a single agent."""
    agent_class = AGENT_REGISTRY.get(agent_type)
    if not agent_class:
        raise ValueError(f"Unknown agent type: {agent_type}")

    agent = agent_class(db)
    return await agent.run(company_id=company_id, period=period)


async def run_full_close(period: str, db: Optional[Session] = None):
    """Run the full month-end close workflow across all companies."""
    if db is None:
        db = SessionLocal()

    try:
        companies = db.query(Company).all()
        results = {}

        logger.info(f"Starting full close workflow for period {period}")

        # Phase 1: Orchestrator initiates
        orchestrator = OrchestratorAgent(db)
        orch_result = await orchestrator.run(period=period, action="full_close")
        results["orchestrator"] = orch_result

        # Phase 2: Per-company parallel agents (Group 1)
        for company in companies:
            cid = company.id
            logger.info(f"Processing {company.name} ({cid})")

            # Trial Balance Validation
            tb_agent = TrialBalanceValidatorAgent(db)
            results[f"tb_{cid}"] = await tb_agent.run(company_id=cid, period=period)

            # Variance Analysis
            var_agent = VarianceAnalysisAgent(db)
            results[f"var_{cid}"] = await var_agent.run(company_id=cid, period=period)

            # Cash Flow Reconciliation
            cf_agent = CashFlowReconciliationAgent(db)
            results[f"cf_{cid}"] = await cf_agent.run(company_id=cid, period=period)

            # Update progress
            company.close_progress = 33.0
            company.close_status = "in_progress"
            db.commit()

        # Phase 3: Sequential per-company (Group 2)
        for company in companies:
            cid = company.id

            # Accrual Verification
            accrual_agent = AccrualVerificationAgent(db)
            results[f"accrual_{cid}"] = await accrual_agent.run(company_id=cid, period=period)

            # Revenue Recognition
            rev_agent = RevenueRecognitionAgent(db)
            results[f"rev_{cid}"] = await rev_agent.run(company_id=cid, period=period)

            # Expense Categorization
            exp_agent = ExpenseCategorizationAgent(db)
            results[f"exp_{cid}"] = await exp_agent.run(company_id=cid, period=period)

            company.close_progress = 66.0
            db.commit()

        # Phase 4: Cross-company (Group 3)
        ic_agent = IntercompanyEliminationAgent(db)
        results["intercompany"] = await ic_agent.run(period=period)

        # Phase 5: Consolidation (Group 4)
        consol_agent = ConsolidationAgent(db)
        results["consolidation"] = await consol_agent.run(period=period)

        # Phase 6: Reporting
        report_agent = ReportingCommunicationAgent(db)
        results["reporting"] = await report_agent.run(period=period)

        # Mark all companies as completed
        for company in companies:
            company.close_progress = 100.0
            company.close_status = "completed"
        db.commit()

        # Send completion email
        await report_agent.run(period=period, report_type="completion_email")

        logger.info(f"Full close workflow completed for period {period}")
        return {"status": "completed", "period": period, "companies_processed": len(companies)}

    except Exception as e:
        logger.error(f"Full close workflow failed: {e}")
        return {"status": "failed", "error": str(e)}


async def run_daily_check(period: str = "2026-01"):
    """Daily autonomous check - scheduled to run at 9 AM."""
    db = SessionLocal()
    try:
        orchestrator = OrchestratorAgent(db)
        await orchestrator.run(period=period, action="health_check")

        # Send daily summary
        reporter = ReportingCommunicationAgent(db)
        await reporter.run(period=period, report_type="daily_email")

        # Send any pending issue alerts
        await reporter.run(period=period, report_type="issue_alert")

        logger.info("Daily check completed")
    finally:
        db.close()


async def run_monitoring():
    """Continuous monitoring - runs every 5 minutes."""
    db = SessionLocal()
    try:
        orchestrator = OrchestratorAgent(db)
        await orchestrator.run(action="monitor_data")
    finally:
        db.close()
