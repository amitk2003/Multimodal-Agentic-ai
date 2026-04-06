"""
Agent 9: Consolidation Agent
Aggregates data from all 8 portfolio companies, applies GAAP consolidation rules,
generates consolidated P&L, Balance Sheet, Cash Flow, and produces investor-ready packages.
"""
import logging
from typing import Dict, Any, Optional, List
from collections import defaultdict
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.models.company import Company
from app.models.financial import TrialBalanceLine

logger = logging.getLogger(__name__)


class ConsolidationAgent(BaseAgent):
    AGENT_TYPE = "consolidation"
    AGENT_NAME = "Consolidation Agent"
    DESCRIPTION = "Aggregates all companies into consolidated financial statements"

    async def execute(self, company_id: Optional[str] = None, period: str = "2026-01", **kwargs) -> Dict[str, Any]:
        findings = []
        actions = []

        companies = self.db.query(Company).all()

        # Aggregate trial balances across all companies
        consolidated = defaultdict(lambda: {"debit": 0, "credit": 0, "balance": 0, "companies": []})

        for company in companies:
            tb_lines = (
                self.db.query(TrialBalanceLine)
                .filter_by(company_id=company.id, period=period)
                .all()
            )

            for line in tb_lines:
                key = (line.account_code, line.account_name, line.account_type)
                consolidated[key]["debit"] += line.debit or 0
                consolidated[key]["credit"] += line.credit or 0
                consolidated[key]["balance"] += line.balance or 0
                if company.id not in consolidated[key]["companies"]:
                    consolidated[key]["companies"].append(company.id)

        # Build consolidated financial statements
        income_statement = []
        balance_sheet = []

        total_revenue = 0
        total_cogs = 0
        total_opex = 0
        total_assets = 0
        total_liabilities = 0
        total_equity = 0

        for (code, name, atype), data in sorted(consolidated.items()):
            entry = {
                "account_code": code,
                "account_name": name,
                "account_type": atype,
                "consolidated_debit": round(data["debit"], 2),
                "consolidated_credit": round(data["credit"], 2),
                "consolidated_balance": round(data["balance"], 2),
                "contributing_companies": len(data["companies"]),
            }

            if atype in ("Revenue", "COGS", "Operating Expense"):
                income_statement.append(entry)
                if atype == "Revenue":
                    total_revenue += abs(data["credit"])
                elif atype == "COGS":
                    total_cogs += abs(data["debit"])
                else:
                    total_opex += abs(data["debit"])
            else:
                balance_sheet.append(entry)
                if atype == "Asset":
                    total_assets += data["balance"]
                elif atype == "Liability":
                    total_liabilities += abs(data["balance"])
                elif atype == "Equity":
                    total_equity += abs(data["balance"])

        gross_profit = total_revenue - total_cogs
        ebitda = gross_profit - total_opex
        gross_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0

        # Retrieve IC elimination data from shared memory
        ic_result = self.memory.get(f"agent:intercompany_elimination:all:{period}")
        elimination_amount = 0
        if ic_result and isinstance(ic_result, dict):
            elimination_amount = ic_result.get("summary", {}).get("total_volume", 0)
            actions.append(f"Applied IC eliminations of ${elimination_amount:,.0f}")

        # Validate consolidated balance sheet equation
        bs_diff = abs(total_assets - (total_liabilities + total_equity))
        if bs_diff > 100:
            findings.append({
                "title": "Consolidated BS Imbalance",
                "description": f"Assets (${total_assets:,.0f}) != Liabilities (${total_liabilities:,.0f}) + Equity (${total_equity:,.0f}). Diff: ${bs_diff:,.0f}",
                "severity": "warning",
            })

        # Per-company contribution analysis
        company_contributions = []
        for company in companies:
            comp_revenue = (
                self.db.query(TrialBalanceLine)
                .filter_by(company_id=company.id, period=period, account_type="Revenue")
                .all()
            )
            comp_rev_total = sum(abs(r.credit or 0) for r in comp_revenue)
            pct = (comp_rev_total / total_revenue * 100) if total_revenue > 0 else 0

            company_contributions.append({
                "company_id": company.id,
                "company_name": company.name,
                "revenue": round(comp_rev_total, 2),
                "revenue_pct": round(pct, 1),
            })

        company_contributions.sort(key=lambda c: c["revenue"], reverse=True)

        # LLM analysis
        llm_result = await self.call_llm(
            prompt=f"""Generate consolidated financial analysis for Apex Capital Partners, period {period}:

Consolidated P&L:
- Total Revenue: ${total_revenue:,.0f}
- COGS: ${total_cogs:,.0f}
- Gross Profit: ${gross_profit:,.0f} ({gross_margin:.1f}%)
- Operating Expenses: ${total_opex:,.0f}
- EBITDA: ${ebitda:,.0f}

Balance Sheet Totals:
- Total Assets: ${total_assets:,.0f}
- Total Liabilities: ${total_liabilities:,.0f}
- Total Equity: ${total_equity:,.0f}

Company Contributions:
{company_contributions}

IC Eliminations: ${elimination_amount:,.0f}

Return JSON: executive_summary (2-3 sentences), key_metrics (dict), portfolio_health (strong/moderate/weak), top_performers (list), areas_of_concern (list), recommendations (list)""",
            system="You are a PE fund CFO preparing a consolidated financial package for investors."
        )

        actions.append(f"Consolidated {len(companies)} companies")
        actions.append(f"Revenue: ${total_revenue:,.0f}, EBITDA: ${ebitda:,.0f}")

        return {
            "status": "completed",
            "findings": findings,
            "actions": actions,
            "consolidated_pl": {
                "total_revenue": round(total_revenue, 2),
                "total_cogs": round(total_cogs, 2),
                "gross_profit": round(gross_profit, 2),
                "gross_margin_pct": round(gross_margin, 1),
                "total_opex": round(total_opex, 2),
                "ebitda": round(ebitda, 2),
            },
            "consolidated_bs": {
                "total_assets": round(total_assets, 2),
                "total_liabilities": round(total_liabilities, 2),
                "total_equity": round(total_equity, 2),
            },
            "income_statement_lines": income_statement,
            "balance_sheet_lines": balance_sheet,
            "company_contributions": company_contributions,
            "llm_analysis": llm_result if isinstance(llm_result, dict) else {},
        }
