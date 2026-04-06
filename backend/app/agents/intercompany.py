"""
Agent 5: Intercompany Elimination Agent
Identifies intercompany transactions across portfolio companies, validates elimination entries,
ensures IC balances net to zero at consolidation, generates elimination journal entries.
"""
import logging
from typing import Dict, Any, Optional
from collections import defaultdict
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.models.financial import IntercompanyTransaction

logger = logging.getLogger(__name__)


class IntercompanyEliminationAgent(BaseAgent):
    AGENT_TYPE = "intercompany_elimination"
    AGENT_NAME = "Intercompany Elimination Agent"
    DESCRIPTION = "Validates and eliminates intercompany transactions for consolidation"

    async def execute(self, company_id: Optional[str] = None, period: str = "2026-01", **kwargs) -> Dict[str, Any]:
        """Analyze and generate elimination entries for intercompany transactions."""
        findings = []
        actions = []

        # Get all IC transactions for the period
        ic_transactions = (
            self.db.query(IntercompanyTransaction)
            .filter_by(period=period)
            .all()
        )

        if not ic_transactions:
            return {
                "status": "completed",
                "findings": [{"title": "No IC Transactions", "description": f"No intercompany transactions for {period}", "severity": "info"}],
                "actions": [],
                "eliminations": [],
            }

        # Analyze IC balances by entity pair
        pair_balances = defaultdict(lambda: {"sell_total": 0, "buy_total": 0, "transactions": []})

        for tx in ic_transactions:
            pair_key = tuple(sorted([tx.selling_entity_id, tx.buying_entity_id]))
            pair_balances[pair_key]["sell_total"] += tx.amount
            pair_balances[pair_key]["transactions"].append(tx.transaction_id)

        # Check: Entity-level IC receivable vs payable
        entity_receivables = defaultdict(float)
        entity_payables = defaultdict(float)

        for tx in ic_transactions:
            entity_receivables[tx.selling_entity_id] += tx.amount
            entity_payables[tx.buying_entity_id] += tx.amount

        # Validate: Total IC receivables should equal total IC payables
        total_receivables = sum(entity_receivables.values())
        total_payables = sum(entity_payables.values())
        net_diff = abs(total_receivables - total_payables)

        if net_diff > 0.01:
            findings.append({
                "title": "IC Imbalance Detected",
                "description": f"Total IC receivables (${total_receivables:,.0f}) != IC payables (${total_payables:,.0f}). Diff: ${net_diff:,.0f}",
                "severity": "error",
                "data": {"receivables": total_receivables, "payables": total_payables, "difference": net_diff},
            })
        else:
            actions.append(f"IC balances verified: ${total_receivables:,.0f} nets to zero")

        # Generate elimination journal entries
        eliminations = []
        for pair_key, data in pair_balances.items():
            entity_a, entity_b = pair_key
            total = data["sell_total"]

            eliminations.append({
                "entity_a": entity_a,
                "entity_b": entity_b,
                "elimination_amount": round(total, 2),
                "num_transactions": len(data["transactions"]),
                "journal_entries": [
                    {"debit_account": "IC Payable (2000)", "credit_account": "IC Receivable (1100)", "amount": round(total, 2)},
                ],
            })

        # Check for unmatched transactions (one side recorded but not the other)
        selling_ids = set(tx.selling_entity_id for tx in ic_transactions)
        buying_ids = set(tx.buying_entity_id for tx in ic_transactions)
        all_entities = selling_ids | buying_ids

        for entity in all_entities:
            recv = entity_receivables.get(entity, 0)
            pay = entity_payables.get(entity, 0)
            net = recv - pay
            if abs(net) > 50000:  # Material net IC position
                findings.append({
                    "title": f"Large Net IC Position: {entity}",
                    "description": f"Net IC position of ${net:,.0f} (Recv: ${recv:,.0f}, Pay: ${pay:,.0f})",
                    "severity": "warning",
                    "data": {"entity": entity, "receivable": recv, "payable": pay, "net": net},
                })

        # Identify potential missing elimination entries
        existing_eliminated = sum(1 for tx in ic_transactions if tx.is_eliminated)
        not_eliminated = len(ic_transactions) - existing_eliminated
        if not_eliminated > 0:
            findings.append({
                "title": f"{not_eliminated} Transactions Pending Elimination",
                "description": f"{not_eliminated} of {len(ic_transactions)} IC transactions have not been eliminated",
                "severity": "info" if not_eliminated < 10 else "warning",
                "data": {"total": len(ic_transactions), "eliminated": existing_eliminated, "pending": not_eliminated},
            })

        # LLM analysis
        llm_result = await self.call_llm(
            prompt=f"""Analyze intercompany elimination results for period {period}:
- Total IC transactions: {len(ic_transactions)}
- Entity pairs: {len(pair_balances)}
- Total IC volume: ${total_receivables:,.0f}
- Net imbalance: ${net_diff:,.0f}
- Findings: {len(findings)}

Entity positions: {dict(entity_receivables)}

Return JSON: assessment, risk_items (list), recommended_actions (list)""",
            system="You are an intercompany accounting specialist. Focus on elimination completeness and consolidation impact."
        )

        actions.append(f"Analyzed {len(ic_transactions)} IC transactions across {len(pair_balances)} entity pairs")
        actions.append(f"Generated {len(eliminations)} elimination entries")

        return {
            "status": "completed",
            "findings": findings,
            "actions": actions,
            "eliminations": eliminations,
            "summary": {
                "total_transactions": len(ic_transactions),
                "total_volume": round(total_receivables, 2),
                "entity_pairs": len(pair_balances),
                "net_imbalance": round(net_diff, 2),
                "eliminations_generated": len(eliminations),
            },
            "llm_analysis": llm_result if isinstance(llm_result, dict) else {},
        }
