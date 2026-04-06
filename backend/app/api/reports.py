"""
Reports & Notifications API - Endpoints for reports, notifications, and exports.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
import csv
import io

from app.database import get_db
from app.models.notification import Notification, Report
from app.models.financial import TrialBalanceLine
from app.models.company import Company

router = APIRouter(prefix="/api", tags=["reports"])


# ---- Notifications ----

@router.get("/notifications")
def get_notifications(
    limit: int = 50,
    offset: int = 0,
    severity: Optional[str] = None,
    unread_only: bool = False,
    db: Session = Depends(get_db),
):
    """Get notifications with filtering."""
    query = db.query(Notification).order_by(desc(Notification.created_at))

    if severity:
        query = query.filter_by(severity=severity)
    if unread_only:
        query = query.filter_by(is_read=False)

    total = query.count()
    notifications = query.offset(offset).limit(limit).all()

    return {
        "notifications": [n.to_dict() for n in notifications],
        "total": total,
        "unread_count": db.query(Notification).filter_by(is_read=False).count(),
    }


@router.put("/notifications/{notification_id}/read")
def mark_notification_read(notification_id: int, db: Session = Depends(get_db)):
    """Mark a notification as read."""
    notif = db.query(Notification).get(notification_id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    db.commit()
    return {"message": "Marked as read"}


@router.put("/notifications/read-all")
def mark_all_notifications_read(db: Session = Depends(get_db)):
    """Mark all notifications as read."""
    db.query(Notification).filter_by(is_read=False).update({"is_read": True})
    db.commit()
    return {"message": "All notifications marked as read"}


# ---- Reports ----

@router.get("/reports")
def get_reports(
    limit: int = 20,
    report_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get generated reports."""
    query = db.query(Report).order_by(desc(Report.created_at))
    if report_type:
        query = query.filter_by(report_type=report_type)

    reports = query.limit(limit).all()
    return {"reports": [r.to_dict() for r in reports]}


@router.get("/reports/{report_id}")
def get_report_detail(report_id: int, db: Session = Depends(get_db)):
    """Get a specific report with full content."""
    report = db.query(Report).get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return {
        **report.to_dict(),
        "content": report.content,
    }


# ---- Exports ----

@router.get("/export/trial-balance/{company_id}")
def export_trial_balance(company_id: str, period: str = "2026-01", db: Session = Depends(get_db)):
    """Export trial balance as CSV."""
    lines = (
        db.query(TrialBalanceLine)
        .filter_by(company_id=company_id, period=period)
        .order_by(TrialBalanceLine.account_code)
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Account Code", "Account Name", "Debit", "Credit", "Balance", "Account Type"])

    for line in lines:
        writer.writerow([line.account_code, line.account_name, line.debit, line.credit, line.balance, line.account_type])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=trial_balance_{company_id}_{period}.csv"},
    )


# ---- Dashboard Summary ----

@router.get("/dashboard/summary")
def get_dashboard_summary(period: str = "2026-01", db: Session = Depends(get_db)):
    """Get aggregate dashboard data for the portfolio."""
    companies = db.query(Company).all()

    total_revenue = 0
    total_ebitda = 0
    company_data = []

    for company in companies:
        tb = (
            db.query(TrialBalanceLine)
            .filter_by(company_id=company.id, period=period)
            .all()
        )
        rev = sum(abs(l.credit or 0) for l in tb if l.account_type == "Revenue")
        cogs = sum(abs(l.debit or 0) for l in tb if l.account_type == "COGS")
        opex = sum(abs(l.debit or 0) for l in tb if l.account_type == "Operating Expense")
        cash = sum(abs(l.balance or 0) for l in tb if l.account_code == 1000)
        ebitda = rev - cogs - opex

        total_revenue += rev
        total_ebitda += ebitda

        issues = db.query(Notification).filter_by(company_id=company.id).filter(
            Notification.severity.in_(["warning", "error", "critical"])
        ).count()

        # Determine traffic light status
        if company.close_status == "completed":
            traffic_light = "green"
        elif issues > 5 or company.close_status == "error":
            traffic_light = "red"
        elif issues > 0 or company.close_status == "in_progress":
            traffic_light = "yellow"
        else:
            traffic_light = "gray"

        company_data.append({
            "id": company.id,
            "name": company.name,
            "industry": company.industry,
            "revenue": round(rev, 2),
            "ebitda": round(ebitda, 2),
            "cash": round(cash, 2),
            "margin": round((ebitda / rev * 100) if rev > 0 else 0, 1),
            "close_status": company.close_status,
            "close_progress": company.close_progress,
            "open_issues": issues,
            "traffic_light": traffic_light,
        })

    # Unread notifications count
    unread_count = db.query(Notification).filter_by(is_read=False).count()

    return {
        "period": period,
        "portfolio": {
            "total_revenue": round(total_revenue, 2),
            "total_ebitda": round(total_ebitda, 2),
            "total_companies": len(companies),
            "companies_completed": len([c for c in companies if c.close_status == "completed"]),
            "companies_in_progress": len([c for c in companies if c.close_status == "in_progress"]),
            "overall_progress": round(
                sum(c.close_progress for c in companies) / len(companies) if companies else 0, 1
            ),
        },
        "companies": company_data,
        "unread_notifications": unread_count,
    }
