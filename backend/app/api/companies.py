"""
Companies API - CRUD endpoints for portfolio companies.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.company import Company
from app.models.financial import TrialBalanceLine
from app.models.notification import Notification

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.get("")
def list_companies(db: Session = Depends(get_db)):
    """Get all portfolio companies with their close status."""
    companies = db.query(Company).all()
    result = []
    for c in companies:
        # Get issue count
        issues = db.query(Notification).filter_by(
            company_id=c.id
        ).filter(Notification.severity.in_(["warning", "error", "critical"])).count()

        data = c.to_dict()
        data["open_issues"] = issues
        result.append(data)

    return {"companies": result, "total": len(result)}


@router.get("/{company_id}")
def get_company(company_id: str, db: Session = Depends(get_db)):
    """Get detailed company information."""
    company = db.query(Company).filter_by(id=company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    issues = db.query(Notification).filter_by(company_id=company_id).filter(
        Notification.severity.in_(["warning", "error", "critical"])
    ).count()

    data = company.to_dict()
    data["open_issues"] = issues
    return data


@router.get("/{company_id}/financials")
def get_company_financials(company_id: str, period: str = "2026-01", db: Session = Depends(get_db)):
    """Get financial statements for a company."""
    company = db.query(Company).filter_by(id=company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Current period
    tb_lines = (
        db.query(TrialBalanceLine)
        .filter_by(company_id=company_id, period=period)
        .order_by(TrialBalanceLine.account_code)
        .all()
    )

    # Prior period
    parts = period.split("-")
    pm = int(parts[1]) - 1
    py = int(parts[0])
    if pm == 0:
        pm = 12
        py -= 1
    prior_period = f"{py}-{pm:02d}"

    prior_lines = (
        db.query(TrialBalanceLine)
        .filter_by(company_id=company_id, period=prior_period)
        .all()
    )
    prior_map = {l.account_code: l for l in prior_lines}

    # Build P&L
    income_statement = []
    balance_sheet = []
    total_revenue = 0
    total_cogs = 0
    total_opex = 0

    for line in tb_lines:
        entry = line.to_dict()
        prior = prior_map.get(line.account_code)
        if prior:
            entry["prior_balance"] = prior.balance
            if line.balance and prior.balance and prior.balance != 0:
                entry["change_pct"] = round(((line.balance - prior.balance) / abs(prior.balance)) * 100, 1)

        if line.account_type in ("Revenue", "COGS", "Operating Expense"):
            income_statement.append(entry)
            if line.account_type == "Revenue":
                total_revenue += abs(line.credit or 0)
            elif line.account_type == "COGS":
                total_cogs += abs(line.debit or 0)
            else:
                total_opex += abs(line.debit or 0)
        else:
            balance_sheet.append(entry)

    gross_profit = total_revenue - total_cogs
    ebitda = gross_profit - total_opex

    return {
        "company_id": company_id,
        "period": period,
        "income_statement": income_statement,
        "balance_sheet": balance_sheet,
        "summary": {
            "revenue": round(total_revenue, 2),
            "cogs": round(total_cogs, 2),
            "gross_profit": round(gross_profit, 2),
            "gross_margin": round((gross_profit / total_revenue * 100) if total_revenue > 0 else 0, 1),
            "opex": round(total_opex, 2),
            "ebitda": round(ebitda, 2),
            "ebitda_margin": round((ebitda / total_revenue * 100) if total_revenue > 0 else 0, 1),
        },
    }


@router.get("/{company_id}/variances")
def get_company_variances(company_id: str, period: str = "2026-01", db: Session = Depends(get_db)):
    """Get variance analysis for a company from agent results."""
    from app.agents.base import shared_memory
    result = shared_memory.get(f"agent:variance_analysis:{company_id}:{period}")
    if not result:
        return {"variances": [], "message": "No variance analysis available. Run agents first."}
    return result
