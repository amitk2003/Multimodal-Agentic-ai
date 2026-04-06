"""
Agent 4: Accrual Verification Agent
Reviews accrued expenses and deferred revenue, verifies supporting data,
calculates amortization, flags missing or incorrect accruals.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.models.financial import AccrualSchedule, TrialBalanceLine

logger = logging.getLogger(__name__)


class AccrualVerificationAgent(BaseAgent):
    AGENT_TYPE = "accrual_verification"
    AGENT_NAME = "Accrual Verification Agent"
    DESCRIPTION = "Verifies accrued expenses, deferred revenue, and amortization schedules"

    async def execute(self, company_id: Optional[str] = None, period: str = "2026-01", **kwargs) -> Dict[str, Any]:
        findings = []
        actions = []

        # Get accrual schedules for this company
        accruals = (
            self.db.query(AccrualSchedule)
            .filter_by(company_id=company_id)
            .all()
        )

        # Get trial balance for accrual-related accounts
        tb_lines = (
            self.db.query(TrialBalanceLine)
            .filter_by(company_id=company_id, period=period)
            .filter(TrialBalanceLine.account_code.in_([2100, 2150, 2200, 6200, 6300, 6400, 6500]))
            .all()
        )
        tb_map = {line.account_code: line for line in tb_lines}

        # Parse period date
        parts = period.split("-")
        period_date = datetime(int(parts[0]), int(parts[1]), 1)

        missing_accruals = []
        stale_accruals = []
        amount_mismatches = []

        for accrual in accruals:
            # Check 1: Is this accrual due for this period?
            is_due = False
            if accrual.frequency == "monthly":
                is_due = True
            elif accrual.frequency == "quarterly":
                is_due = period_date.month in [3, 6, 9, 12]
            elif accrual.frequency == "annual":
                is_due = period_date.month == 12

            if not is_due:
                continue

            # Check 2: Last booked date - is it stale?
            if accrual.last_booked_date:
                try:
                    last_booked = datetime.strptime(accrual.last_booked_date, "%Y-%m-%d")
                    days_since = (period_date - last_booked).days

                    if accrual.frequency == "monthly" and days_since > 45:
                        stale_accruals.append(accrual)
                        findings.append({
                            "title": f"Stale Accrual: {accrual.accrual_type}",
                            "description": f"Last booked {days_since} days ago on {accrual.last_booked_date}. Expected monthly booking.",
                            "severity": "warning",
                            "data": {
                                "accrual_type": accrual.accrual_type,
                                "gl_account": accrual.gl_account,
                                "amount": accrual.amount,
                                "last_booked": accrual.last_booked_date,
                                "days_overdue": days_since,
                            },
                        })
                    elif accrual.frequency == "annual" and days_since > 380:
                        stale_accruals.append(accrual)
                        findings.append({
                            "title": f"Missing Annual Accrual: {accrual.accrual_type}",
                            "description": f"Annual accrual not booked. Last booking was {accrual.last_booked_date}",
                            "severity": "error",
                            "data": {
                                "accrual_type": accrual.accrual_type,
                                "gl_account": accrual.gl_account,
                                "amount": accrual.amount,
                            },
                        })
                except ValueError:
                    pass

            # Check 3: GL account balance vs expected accrual amount
            tb_line = tb_map.get(accrual.gl_account)
            if tb_line and accrual.amount > 0:
                gl_balance = abs(tb_line.balance or 0)
                if gl_balance > 0:
                    diff_pct = abs(gl_balance - accrual.amount) / accrual.amount
                    if diff_pct > 0.25:  # More than 25% difference
                        amount_mismatches.append({
                            "accrual": accrual.accrual_type,
                            "expected": accrual.amount,
                            "actual_gl": gl_balance,
                            "difference_pct": round(diff_pct * 100, 1),
                        })

        # Check for specific missing December accruals (bonus, etc.)
        if period_date.month == 12 or period_date.month == 1:
            bonus_accruals = [a for a in accruals if "bonus" in a.accrual_type.lower()]
            if not bonus_accruals:
                findings.append({
                    "title": "Missing Bonus Accrual",
                    "description": "No year-end bonus accrual found. This is commonly required for December close.",
                    "severity": "error",
                    "data": {"period": period, "expected_account": 6000},
                })

        # Check for missing rent accrual
        rent_accruals = [a for a in accruals if "rent" in a.accrual_type.lower()]
        if not rent_accruals:
            findings.append({
                "title": "No Rent Accrual Schedule",
                "description": "No rent expense accrual found. Verify if rent is prepaid or accrued.",
                "severity": "info",
            })

        if amount_mismatches:
            for mm in amount_mismatches[:5]:
                findings.append({
                    "title": f"Accrual Amount Mismatch: {mm['accrual']}",
                    "description": f"Expected ${mm['expected']:,.0f} but GL shows ${mm['actual_gl']:,.0f} ({mm['difference_pct']}% diff)",
                    "severity": "warning",
                    "data": mm,
                })

        # LLM analysis
        llm_result = await self.call_llm(
            prompt=f"""Review accrual verification results for {company_id}, period {period}:
- Total accrual schedules: {len(accruals)}
- Stale accruals: {len(stale_accruals)}
- Amount mismatches: {len(amount_mismatches)}
- Missing findings: {len(findings)}

Return JSON with: assessment, recommendations (list), suggested_journal_entries (list of dicts with debit_account, credit_account, amount, description)""",
            system="You are an accounting specialist reviewing accrual completeness."
        )

        actions.append(f"Reviewed {len(accruals)} accrual schedules")
        actions.append(f"Identified {len(stale_accruals)} stale accruals")
        actions.append(f"Found {len(amount_mismatches)} amount mismatches")

        return {
            "status": "completed",
            "findings": findings,
            "actions": actions,
            "summary": {
                "total_accruals": len(accruals),
                "stale_count": len(stale_accruals),
                "mismatches": len(amount_mismatches),
                "missing_count": len([f for f in findings if f["severity"] in ("error", "critical")]),
            },
            "llm_analysis": llm_result if isinstance(llm_result, dict) else {},
        }
