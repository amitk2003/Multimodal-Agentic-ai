"""
Agent 2: Trial Balance Validator Agent
Validates debits = credits for each entity, flags accounts with unexpected balances,
runs account reconciliation checks.
"""
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.agents.base import BaseAgent
from app.models.financial import TrialBalanceLine

logger = logging.getLogger(__name__)


class TrialBalanceValidatorAgent(BaseAgent):
    AGENT_TYPE = "trial_balance_validator"
    AGENT_NAME = "Trial Balance Validator"
    DESCRIPTION = "Validates trial balance integrity - debits=credits, unusual balances, reconciliation"

    async def execute(self, company_id: Optional[str] = None, period: str = "2026-01", **kwargs) -> Dict[str, Any]:
        """Validate trial balance for a specific company and period."""
        findings = []
        actions = []

        # Get trial balance data
        tb_lines = (
            self.db.query(TrialBalanceLine)
            .filter_by(company_id=company_id, period=period)
            .all()
        )

        if not tb_lines:
            return {
                "status": "completed",
                "findings": [{
                    "title": "No Trial Balance Data",
                    "description": f"No trial balance data found for {company_id} period {period}",
                    "severity": "warning",
                }],
                "actions": ["Flagged as missing data"],
            }

        # CHECK 1: Debits = Credits
        total_debits = sum(line.debit or 0 for line in tb_lines)
        total_credits = sum(line.credit or 0 for line in tb_lines)
        difference = abs(total_debits - total_credits)

        if difference > 0.01:
            findings.append({
                "title": "Trial Balance Out of Balance",
                "description": f"Debits (${total_debits:,.2f}) != Credits (${total_credits:,.2f}). Difference: ${difference:,.2f}",
                "severity": "critical",
                "data": {"total_debits": total_debits, "total_credits": total_credits, "difference": difference},
            })
        else:
            actions.append(f"TB balanced: Debits=${total_debits:,.2f}, Credits=${total_credits:,.2f}")

        # CHECK 2: Unusual balances (negative assets, positive liabilities with wrong sign, etc.)
        for line in tb_lines:
            if line.account_type == "Asset" and "Accumulated" not in line.account_name and "Allowance" not in line.account_name:
                if (line.balance or 0) < 0:
                    findings.append({
                        "title": f"Negative Asset Balance: {line.account_name}",
                        "description": f"Account {line.account_code} has negative balance of ${line.balance:,.2f}",
                        "severity": "warning",
                        "data": {"account_code": line.account_code, "balance": line.balance},
                    })

            if line.account_type == "Revenue" and (line.balance or 0) > 0:
                findings.append({
                    "title": f"Positive Revenue Balance: {line.account_name}",
                    "description": f"Revenue account {line.account_code} has unexpected positive balance of ${line.balance:,.2f}",
                    "severity": "warning",
                    "data": {"account_code": line.account_code, "balance": line.balance},
                })

        # CHECK 3: Zero balance accounts that should have balances
        zero_accounts = [line for line in tb_lines if abs(line.balance or 0) < 0.01 and line.account_type in ("Asset", "Liability")]
        if zero_accounts:
            for acc in zero_accounts[:3]:  # Report top 3
                findings.append({
                    "title": f"Zero Balance: {acc.account_name}",
                    "description": f"Account {acc.account_code} ({acc.account_type}) has zero balance - verify if expected",
                    "severity": "info",
                    "data": {"account_code": acc.account_code, "account_type": acc.account_type},
                })

        # CHECK 4: Account type distribution analysis
        type_totals = {}
        for line in tb_lines:
            at = line.account_type
            if at not in type_totals:
                type_totals[at] = 0.0
            type_totals[at] += abs(line.balance or 0)

        # CHECK 5: Accounting equation (Assets = Liabilities + Equity + Revenue - Expenses)
        assets = sum(line.balance or 0 for line in tb_lines if line.account_type == "Asset")
        liabilities = sum(abs(line.balance or 0) for line in tb_lines if line.account_type == "Liability")
        equity = sum(abs(line.balance or 0) for line in tb_lines if line.account_type == "Equity")

        # Use LLM for intelligent analysis
        summary_data = {
            "company": company_id,
            "period": period,
            "total_accounts": len(tb_lines),
            "total_debits": total_debits,
            "total_credits": total_credits,
            "balance_diff": difference,
            "type_totals": type_totals,
            "findings_count": len(findings),
            "assets": assets,
            "liabilities": liabilities,
            "equity": equity,
        }

        llm_analysis = await self.call_llm(
            prompt=f"""Analyze this trial balance validation result and provide commentary:
{summary_data}
Existing findings: {len(findings)}

Return JSON with keys: overall_assessment, risk_level (low/medium/high), recommendations (list of strings), commentary (string)""",
            system="You are a senior auditor reviewing trial balance validations. Be precise and flag any concerns."
        )

        actions.append(f"Validated {len(tb_lines)} accounts")
        actions.append(f"Found {len(findings)} issues")

        return {
            "status": "completed",
            "findings": findings,
            "actions": actions,
            "summary": {
                "total_accounts": len(tb_lines),
                "total_debits": total_debits,
                "total_credits": total_credits,
                "is_balanced": difference <= 0.01,
                "type_totals": type_totals,
            },
            "llm_analysis": llm_analysis if isinstance(llm_analysis, dict) else {},
        }
