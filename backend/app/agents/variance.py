"""
Agent 3: Variance Analysis Agent
Compares actual vs. budget and actual vs. prior month.
Identifies variances >10% or >$50K, generates AI commentary, prioritizes variances.
"""
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.models.financial import TrialBalanceLine, Budget
from app.config import settings

logger = logging.getLogger(__name__)


class VarianceAnalysisAgent(BaseAgent):
    AGENT_TYPE = "variance_analysis"
    AGENT_NAME = "Variance Analysis Agent"
    DESCRIPTION = "Compares actual vs budget/prior period, identifies material variances"

    async def execute(self, company_id: Optional[str] = None, period: str = "2026-01", **kwargs) -> Dict[str, Any]:
        """Perform variance analysis for a company."""
        findings = []
        actions = []
        variances = []

        # Get actual trial balance for the period
        actuals = (
            self.db.query(TrialBalanceLine)
            .filter_by(company_id=company_id, period=period)
            .filter(TrialBalanceLine.account_type.in_(["Revenue", "COGS", "Operating Expense"]))
            .all()
        )

        if not actuals:
            return {
                "status": "completed",
                "findings": [{"title": "No Data", "description": "No P&L data found", "severity": "warning"}],
                "actions": [],
                "variances": [],
            }

        # Parse period to get month/year for budget lookup
        parts = period.split("-")
        year = int(parts[0])
        month = int(parts[1])

        # Get budget data
        budgets = (
            self.db.query(Budget)
            .filter_by(company_id=company_id, year=year, month=month)
            .all()
        )
        budget_map = {b.account_code: b.budget_amount for b in budgets}

        # Get prior period data
        prior_month = month - 1
        prior_year = year
        if prior_month == 0:
            prior_month = 12
            prior_year -= 1
        prior_period = f"{prior_year}-{prior_month:02d}"

        prior_actuals = (
            self.db.query(TrialBalanceLine)
            .filter_by(company_id=company_id, period=prior_period)
            .filter(TrialBalanceLine.account_type.in_(["Revenue", "COGS", "Operating Expense"]))
            .all()
        )
        prior_map = {pa.account_code: abs(pa.balance or 0) for pa in prior_actuals}

        # Analyze each account
        threshold_pct = settings.VARIANCE_THRESHOLD_PCT / 100
        threshold_amt = settings.VARIANCE_THRESHOLD_AMT

        for actual in actuals:
            actual_amount = abs(actual.balance or 0)
            if actual.account_type == "Revenue":
                actual_amount = abs(actual.credit or 0)
            else:
                actual_amount = abs(actual.debit or 0)

            # Budget variance
            budget_amount = budget_map.get(actual.account_code, 0)
            if budget_amount > 0:
                budget_var_amt = actual_amount - budget_amount
                budget_var_pct = (budget_var_amt / budget_amount) if budget_amount != 0 else 0

                is_material = abs(budget_var_pct) > threshold_pct or abs(budget_var_amt) > threshold_amt

                variance_entry = {
                    "account_code": actual.account_code,
                    "account_name": actual.account_name,
                    "account_type": actual.account_type,
                    "actual": round(actual_amount, 2),
                    "budget": round(budget_amount, 2),
                    "variance_amount": round(budget_var_amt, 2),
                    "variance_pct": round(budget_var_pct * 100, 1),
                    "is_material": is_material,
                    "direction": "over" if budget_var_amt > 0 else "under",
                }

                # Add prior period comparison
                prior_amount = prior_map.get(actual.account_code, 0)
                if prior_amount > 0:
                    mom_var = actual_amount - prior_amount
                    mom_pct = (mom_var / prior_amount) if prior_amount != 0 else 0
                    variance_entry["prior_period"] = round(prior_amount, 2)
                    variance_entry["mom_variance"] = round(mom_var, 2)
                    variance_entry["mom_variance_pct"] = round(mom_pct * 100, 1)

                variances.append(variance_entry)

                if is_material:
                    direction = "over budget" if budget_var_amt > 0 else "under budget"
                    findings.append({
                        "title": f"Material Variance: {actual.account_name}",
                        "description": f"{actual.account_name} is ${abs(budget_var_amt):,.0f} ({abs(budget_var_pct)*100:.1f}%) {direction}",
                        "severity": "warning" if abs(budget_var_pct) < 0.2 else "error",
                        "data": variance_entry,
                    })

        # Sort variances by absolute amount
        variances.sort(key=lambda v: abs(v.get("variance_amount", 0)), reverse=True)

        # Use LLM for variance commentary on top variances
        top_variances = variances[:10]
        if top_variances:
            llm_result = await self.call_llm(
                prompt=f"""Analyze these top {len(top_variances)} variances for {company_id} in period {period}.
For each material variance, provide a likely explanation and recommendation.

Variances:
{top_variances}

Return JSON with keys:
- commentary: overall variance narrative (2-3 sentences)
- top_concerns: list of dicts with keys (account_name, explanation, recommendation, risk_level)
- overall_risk: low/medium/high""",
                system="You are a PE fund financial analyst. Provide concise, actionable variance commentary."
            )
        else:
            llm_result = {"commentary": "No material variances detected.", "overall_risk": "low"}

        actions.append(f"Analyzed {len(actuals)} P&L accounts")
        actions.append(f"Found {len([v for v in variances if v.get('is_material')])} material variances")

        return {
            "status": "completed",
            "findings": findings,
            "actions": actions,
            "variances": variances,
            "top_variances": top_variances,
            "llm_commentary": llm_result if isinstance(llm_result, dict) else {},
            "summary": {
                "total_accounts_analyzed": len(actuals),
                "material_variances": len([v for v in variances if v.get("is_material")]),
                "total_favorable": len([v for v in variances if v.get("variance_amount", 0) < 0]),
                "total_unfavorable": len([v for v in variances if v.get("variance_amount", 0) > 0]),
            },
        }
