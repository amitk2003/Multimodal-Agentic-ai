"""
Agent 8: Cash Flow Reconciliation Agent
Reconciles cash accounts to bank statements, identifies outstanding items,
validates cash flow statement calculations, flags unusual cash movements.
"""
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.models.financial import TrialBalanceLine, BankStatement

logger = logging.getLogger(__name__)


class CashFlowReconciliationAgent(BaseAgent):
    AGENT_TYPE = "cash_flow_reconciliation"
    AGENT_NAME = "Cash Flow Reconciliation Agent"
    DESCRIPTION = "Reconciles cash accounts to bank statements and validates cash flow"

    async def execute(self, company_id: Optional[str] = None, period: str = "2026-01", **kwargs) -> Dict[str, Any]:
        findings = []
        actions = []

        # Get GL cash balance
        cash_gl = (
            self.db.query(TrialBalanceLine)
            .filter_by(company_id=company_id, period=period, account_code=1000)
            .first()
        )
        gl_cash_balance = abs(cash_gl.balance or 0) if cash_gl else 0

        # Get bank statement data
        bank_entries = (
            self.db.query(BankStatement)
            .filter_by(company_id=company_id, period=period)
            .order_by(BankStatement.date)
            .all()
        )

        if not bank_entries:
            return {
                "status": "completed",
                "findings": [{"title": "No Bank Data", "description": "No bank statement data found", "severity": "warning"}],
                "actions": [],
            }

        # Get ending bank balance (last entry)
        bank_ending_balance = bank_entries[-1].balance if bank_entries else 0
        bank_beginning_balance = bank_entries[0].balance if bank_entries else 0

        # Check 1: GL vs Bank reconciliation
        recon_diff = abs(gl_cash_balance - bank_ending_balance)
        if recon_diff > 100:  # Allow small rounding
            findings.append({
                "title": "Cash Reconciliation Difference",
                "description": f"GL cash (${gl_cash_balance:,.0f}) differs from bank ending balance (${bank_ending_balance:,.0f}) by ${recon_diff:,.0f}",
                "severity": "warning" if recon_diff < 50000 else "error",
                "data": {"gl_balance": gl_cash_balance, "bank_balance": bank_ending_balance, "difference": recon_diff},
            })
        else:
            actions.append(f"Cash reconciled: GL=${gl_cash_balance:,.0f} matches Bank=${bank_ending_balance:,.0f}")

        # Check 2: Analyze bank transactions for unusual items
        total_deposits = sum(e.credit or 0 for e in bank_entries if e.credit)
        total_withdrawals = sum(e.debit or 0 for e in bank_entries if e.debit)
        net_cash_flow = total_deposits - total_withdrawals

        # Check 3: Identify large transactions
        large_transactions = []
        for entry in bank_entries:
            amount = (entry.debit or 0) + (entry.credit or 0)
            if amount > 200000:  # Large transaction threshold
                large_transactions.append({
                    "date": entry.date,
                    "description": entry.description,
                    "amount": amount,
                    "type": "withdrawal" if entry.debit else "deposit",
                })

        if large_transactions:
            findings.append({
                "title": f"{len(large_transactions)} Large Cash Transactions",
                "description": f"Found {len(large_transactions)} transactions over $200K requiring verification",
                "severity": "info",
                "data": {"transactions": large_transactions[:5]},
            })

        # Check 4: Negative cash balance check
        min_balance = min(e.balance for e in bank_entries)
        if min_balance < 0:
            findings.append({
                "title": "Negative Cash Balance",
                "description": f"Cash balance went negative during the month (min: ${min_balance:,.0f}). Potential overdraft.",
                "severity": "error",
                "data": {"min_balance": min_balance},
            })

        # Check 5: Cash flow summary (indirect method approximation)
        # Get P&L items for operating cash flow
        pl_lines = (
            self.db.query(TrialBalanceLine)
            .filter_by(company_id=company_id, period=period)
            .filter(TrialBalanceLine.account_type.in_(["Revenue", "COGS", "Operating Expense"]))
            .all()
        )
        revenue = sum(abs(l.credit or 0) for l in pl_lines if l.account_type == "Revenue")
        expenses = sum(abs(l.debit or 0) for l in pl_lines if l.account_type in ("COGS", "Operating Expense"))
        net_income = revenue - expenses

        # Get depreciation/amortization (non-cash)
        dep_amor = sum(
            abs(l.debit or 0) for l in pl_lines
            if any(kw in l.account_name.lower() for kw in ["depreciation", "amortization"])
        )

        operating_cf_approx = net_income + dep_amor

        # LLM analysis
        llm_result = await self.call_llm(
            prompt=f"""Analyze cash flow reconciliation for {company_id}, period {period}:
- GL Cash: ${gl_cash_balance:,.0f}
- Bank Ending Balance: ${bank_ending_balance:,.0f}
- Reconciliation Difference: ${recon_diff:,.0f}
- Total Deposits: ${total_deposits:,.0f}
- Total Withdrawals: ${total_withdrawals:,.0f}
- Net Cash Flow: ${net_cash_flow:,.0f}
- Net Income: ${net_income:,.0f}
- Operating CF (approx): ${operating_cf_approx:,.0f}
- Large Transactions: {len(large_transactions)}
- Outstanding Items: {len(findings)}

Return JSON: assessment, reconciling_items (list of potential items), cash_flow_commentary, liquidity_risk (low/medium/high), recommendations (list)""",
            system="You are a treasury analyst performing cash reconciliation and cash flow analysis."
        )

        actions.append(f"Analyzed {len(bank_entries)} bank transactions")
        actions.append(f"Deposits: ${total_deposits:,.0f}, Withdrawals: ${total_withdrawals:,.0f}")

        return {
            "status": "completed",
            "findings": findings,
            "actions": actions,
            "summary": {
                "gl_cash_balance": round(gl_cash_balance, 2),
                "bank_ending_balance": round(bank_ending_balance, 2),
                "reconciliation_diff": round(recon_diff, 2),
                "total_deposits": round(total_deposits, 2),
                "total_withdrawals": round(total_withdrawals, 2),
                "net_cash_flow": round(net_cash_flow, 2),
                "net_income": round(net_income, 2),
                "operating_cf_approx": round(operating_cf_approx, 2),
                "large_transactions_count": len(large_transactions),
            },
            "llm_analysis": llm_result if isinstance(llm_result, dict) else {},
        }
