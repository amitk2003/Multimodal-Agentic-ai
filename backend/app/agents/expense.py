"""
Agent 7: Expense Categorization Agent
Reviews expense GL accounts, reclassifies miscategorized expenses,
validates department/cost center allocations, suggests chart of accounts improvements.
"""
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.models.financial import TrialBalanceLine

logger = logging.getLogger(__name__)

# Define expected expense categories with typical account code ranges
EXPENSE_CATEGORIES = {
    "COGS": {"codes": range(5000, 5400), "names": ["cost of goods", "cost of services", "materials", "labor", "overhead"]},
    "Personnel": {"codes": range(6000, 6200), "names": ["salaries", "wages", "benefits", "payroll", "bonus", "commission"]},
    "Facilities": {"codes": range(6200, 6500), "names": ["rent", "utilities", "insurance", "maintenance"]},
    "Professional": {"codes": range(6500, 6600), "names": ["professional", "legal", "audit", "consulting", "contractor"]},
    "Sales & Marketing": {"codes": range(7000, 7300), "names": ["sales", "marketing", "advertising", "travel", "entertainment"]},
    "R&D": {"codes": range(8000, 8100), "names": ["research", "development"]},
    "D&A": {"codes": range(9000, 9200), "names": ["depreciation", "amortization"]},
    "Finance": {"codes": range(9500, 9600), "names": ["interest"]},
}


class ExpenseCategorizationAgent(BaseAgent):
    AGENT_TYPE = "expense_categorization"
    AGENT_NAME = "Expense Categorization Agent"
    DESCRIPTION = "Reviews and validates expense categorization across GL accounts"

    async def execute(self, company_id: Optional[str] = None, period: str = "2026-01", **kwargs) -> Dict[str, Any]:
        findings = []
        actions = []
        reclassifications = []

        # Get all expense lines
        expense_lines = (
            self.db.query(TrialBalanceLine)
            .filter_by(company_id=company_id, period=period)
            .filter(TrialBalanceLine.account_type.in_(["COGS", "Operating Expense"]))
            .all()
        )

        if not expense_lines:
            return {"status": "completed", "findings": [], "actions": ["No expense data found"], "reclassifications": []}

        total_expenses = sum(abs(line.debit or 0) for line in expense_lines)

        # Check 1: Miscategorized expenses based on name vs account code
        for line in expense_lines:
            name_lower = line.account_name.lower()
            code = line.account_code

            # Check if name matches expected category for its code
            for category, info in EXPENSE_CATEGORIES.items():
                name_match = any(keyword in name_lower for keyword in info["names"])
                code_match = code in info["codes"]

                if name_match and not code_match:
                    amount = abs(line.debit or 0)
                    if amount > 1000:  # Only flag material items
                        expected_code = list(info["codes"])[0]
                        reclassifications.append({
                            "account_code": code,
                            "account_name": line.account_name,
                            "current_type": line.account_type,
                            "suggested_category": category,
                            "suggested_code_range": f"{info['codes'].start}-{info['codes'].stop}",
                            "amount": round(amount, 2),
                        })
                        findings.append({
                            "title": f"Potential Misclassification: {line.account_name}",
                            "description": f"Account {code} ({line.account_name}) appears to be {category} but is coded under {line.account_type}. Amount: ${amount:,.0f}",
                            "severity": "warning",
                            "data": {"account_code": code, "suggested_category": category, "amount": amount},
                        })
                    break

        # Check 2: COGS items that look like operating expenses
        cogs_lines = [l for l in expense_lines if l.account_type == "COGS"]
        for line in cogs_lines:
            name_lower = line.account_name.lower()
            opex_keywords = ["marketing", "sales", "travel", "advertising", "rent", "software"]
            if any(kw in name_lower for kw in opex_keywords):
                amount = abs(line.debit or 0)
                findings.append({
                    "title": f"COGS Contains OpEx: {line.account_name}",
                    "description": f"'{line.account_name}' is classified as COGS but appears to be an operating expense (${amount:,.0f}). This affects gross margin accuracy.",
                    "severity": "error",
                    "data": {"account_code": line.account_code, "amount": amount, "impact": "gross_margin"},
                })

        # Check 3: Expense distribution analysis
        expense_by_type = {}
        for line in expense_lines:
            atype = line.account_type
            if atype not in expense_by_type:
                expense_by_type[atype] = 0
            expense_by_type[atype] += abs(line.debit or 0)

        # Check 4: Large single-line expenses relative to total
        for line in expense_lines:
            amount = abs(line.debit or 0)
            if total_expenses > 0 and amount / total_expenses > 0.3:
                findings.append({
                    "title": f"Expense Concentration: {line.account_name}",
                    "description": f"{line.account_name} is {amount/total_expenses*100:.0f}% of total expenses (${amount:,.0f}). Verify allocation.",
                    "severity": "info",
                })

        # LLM analysis for chart of accounts suggestions
        llm_result = await self.call_llm(
            prompt=f"""Review expense categorization for {company_id}, period {period}:
- Total expenses: ${total_expenses:,.0f}
- Expense accounts: {len(expense_lines)}
- Potential reclassifications found: {len(reclassifications)}
- Expense distribution: {expense_by_type}

Reclassifications: {reclassifications[:5]}

Return JSON: assessment, chart_of_accounts_suggestions (list), reclassification_impact (dict with gross_margin_impact, ebitda_impact), recommendations (list)""",
            system="You are a financial controller reviewing expense categorization. Focus on GAAP compliance and reporting accuracy."
        )

        actions.append(f"Reviewed {len(expense_lines)} expense accounts totaling ${total_expenses:,.0f}")
        actions.append(f"Found {len(reclassifications)} potential reclassifications")

        return {
            "status": "completed",
            "findings": findings,
            "actions": actions,
            "reclassifications": reclassifications,
            "summary": {
                "total_expenses": round(total_expenses, 2),
                "accounts_reviewed": len(expense_lines),
                "reclassifications": len(reclassifications),
                "expense_distribution": expense_by_type,
            },
            "llm_analysis": llm_result if isinstance(llm_result, dict) else {},
        }
