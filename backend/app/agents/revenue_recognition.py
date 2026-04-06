"""
Agent 6: Revenue Recognition Agent
Validates revenue recognition per ASC 606, checks contract terms,
performance obligations, identifies timing issues, suggests adjusting entries.
"""
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.models.financial import TrialBalanceLine

logger = logging.getLogger(__name__)


class RevenueRecognitionAgent(BaseAgent):
    AGENT_TYPE = "revenue_recognition"
    AGENT_NAME = "Revenue Recognition Agent"
    DESCRIPTION = "Validates revenue recognition compliance with ASC 606"

    async def execute(self, company_id: Optional[str] = None, period: str = "2026-01", **kwargs) -> Dict[str, Any]:
        findings = []
        actions = []

        # Get revenue accounts
        revenue_lines = (
            self.db.query(TrialBalanceLine)
            .filter_by(company_id=company_id, period=period)
            .filter(TrialBalanceLine.account_type == "Revenue")
            .all()
        )

        # Get deferred revenue
        deferred_rev = (
            self.db.query(TrialBalanceLine)
            .filter_by(company_id=company_id, period=period, account_code=2200)
            .first()
        )

        total_revenue = sum(abs(r.credit or 0) for r in revenue_lines)
        deferred_amount = abs(deferred_rev.balance or 0) if deferred_rev else 0

        # Get prior period revenue for trend
        parts = period.split("-")
        prior_month = int(parts[1]) - 1
        prior_year = int(parts[0])
        if prior_month == 0:
            prior_month = 12
            prior_year -= 1
        prior_period = f"{prior_year}-{prior_month:02d}"

        prior_revenue = (
            self.db.query(TrialBalanceLine)
            .filter_by(company_id=company_id, period=prior_period)
            .filter(TrialBalanceLine.account_type == "Revenue")
            .all()
        )
        prior_total = sum(abs(r.credit or 0) for r in prior_revenue)

        # Check 1: Revenue growth reasonableness
        if prior_total > 0:
            growth = (total_revenue - prior_total) / prior_total
            if abs(growth) > 0.25:  # More than 25% MoM change
                findings.append({
                    "title": "Unusual Revenue Change",
                    "description": f"Revenue changed by {growth*100:.1f}% MoM (${total_revenue:,.0f} vs ${prior_total:,.0f}). Verify revenue timing.",
                    "severity": "warning",
                    "data": {"current": total_revenue, "prior": prior_total, "growth_pct": round(growth * 100, 1)},
                })

        # Check 2: Deferred revenue ratio
        if total_revenue > 0 and deferred_amount > 0:
            deferred_ratio = deferred_amount / total_revenue
            if deferred_ratio > 3.0:
                findings.append({
                    "title": "High Deferred Revenue",
                    "description": f"Deferred revenue (${deferred_amount:,.0f}) is {deferred_ratio:.1f}x monthly revenue. Review for proper recognition.",
                    "severity": "warning",
                    "data": {"deferred": deferred_amount, "revenue": total_revenue, "ratio": round(deferred_ratio, 2)},
                })

        # Check 3: Revenue concentration by account
        if len(revenue_lines) > 1:
            for line in revenue_lines:
                line_amount = abs(line.credit or 0)
                if total_revenue > 0 and line_amount / total_revenue > 0.95:
                    findings.append({
                        "title": "Revenue Concentration Risk",
                        "description": f"Account {line.account_name} represents {line_amount/total_revenue*100:.0f}% of total revenue",
                        "severity": "info",
                    })

        # ASC 606 analysis via LLM
        llm_result = await self.call_llm(
            prompt=f"""Perform ASC 606 revenue recognition review for {company_id}, period {period}:
- Total revenue: ${total_revenue:,.0f}
- Revenue accounts: {[{'name': r.account_name, 'amount': abs(r.credit or 0)} for r in revenue_lines]}
- Deferred revenue: ${deferred_amount:,.0f}
- Prior period revenue: ${prior_total:,.0f}
- MoM growth: {((total_revenue - prior_total) / prior_total * 100) if prior_total > 0 else 0:.1f}%

Evaluate: Step 1 (contracts), Step 2 (performance obligations), Step 3 (transaction price), Step 4 (allocation), Step 5 (recognition timing)

Return JSON: asc606_assessment, risk_areas (list), adjusting_entries (list with debit_account, credit_account, amount, reason), compliance_score (0-100)""",
            system="You are a revenue recognition specialist reviewing ASC 606 compliance for PE portfolio companies."
        )

        actions.append(f"Reviewed {len(revenue_lines)} revenue accounts totaling ${total_revenue:,.0f}")
        actions.append(f"Deferred revenue: ${deferred_amount:,.0f}")

        return {
            "status": "completed",
            "findings": findings,
            "actions": actions,
            "summary": {
                "total_revenue": round(total_revenue, 2),
                "deferred_revenue": round(deferred_amount, 2),
                "prior_revenue": round(prior_total, 2),
                "revenue_accounts": len(revenue_lines),
            },
            "llm_analysis": llm_result if isinstance(llm_result, dict) else {},
        }
