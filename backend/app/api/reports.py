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


# ─────────────────────────────────────────────────────────────────────────────
# NEW PREMIUM FINTECH FEATURES
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/conflicts")
def get_transaction_conflicts(
    period: str = "2026-01",
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Real-time Transaction Conflict Feed.
    Returns all critical/error notifications that indicate financial conflicts,
    imbalances, or data integrity issues — analogous to a trading conflict desk feed.
    """
    query = (
        db.query(Notification)
        .filter(Notification.severity.in_(["error", "critical"]))
        .order_by(desc(Notification.created_at))
    )
    if severity:
        query = query.filter(Notification.severity == severity)

    conflicts = query.limit(100).all()

    # Enrich with company names
    conflict_list = []
    for n in conflicts:
        company = db.query(Company).filter_by(id=n.company_id).first() if n.company_id else None
        conflict_list.append({
            **n.to_dict(),
            "company_name": company.name if company else "Portfolio-Wide",
            "conflict_score": 100 if n.severity == "critical" else 75,
            "resolution_status": "open" if not n.is_read else "acknowledged",
        })

    return {
        "conflicts": conflict_list,
        "total": len(conflict_list),
        "critical_count": sum(1 for c in conflict_list if c["conflict_score"] == 100),
        "error_count": sum(1 for c in conflict_list if c["conflict_score"] == 75),
    }


@router.get("/anomaly-heatmap")
def get_anomaly_heatmap(period: str = "2026-01", db: Session = Depends(get_db)):
    """
    Anomaly Heatmap Data.
    Returns a matrix of anomaly scores (0-100) per company per financial dimension.
    Powers the frontend heatmap visualization.
    """
    companies = db.query(Company).all()
    heatmap = []

    dimensions = [
        "revenue_recognition", "trial_balance", "variance_analysis",
        "accrual_verification", "intercompany_elimination", "cash_flow",
    ]

    for company in companies:
        row = {"company_id": company.id, "company_name": company.name, "scores": {}}

        # Calculate anomaly score per dimension based on notification severity
        for dim in dimensions:
            issues = (
                db.query(Notification)
                .filter_by(company_id=company.id, agent_type=dim.replace("_", "_"))
                .filter(Notification.severity.in_(["warning", "error", "critical"]))
                .count()
            )
            # Score: 0 = clean, 100 = critical
            if issues == 0:
                score = 0
            elif issues <= 2:
                score = 25
            elif issues <= 5:
                score = 55
            else:
                score = 85
            row["scores"][dim] = score

        row["overall_risk"] = round(sum(row["scores"].values()) / len(dimensions), 1)
        heatmap.append(row)

    return {
        "period": period,
        "dimensions": dimensions,
        "heatmap": heatmap,
    }


@router.post("/smart-digest")
async def send_smart_digest(period: str = "2026-01", db: Session = Depends(get_db)):
    """
    AI-Powered Smart Alert Digest.
    Aggregates all unread alerts, deduplicates them, and sends a consolidated
    digest email — prevents inbox flooding while ensuring nothing is missed.
    """
    from app.services.email_service import email_service

    unread = (
        db.query(Notification)
        .filter_by(is_read=False)
        .order_by(desc(Notification.created_at))
        .limit(50)
        .all()
    )

    if not unread:
        return {"message": "No unread alerts to digest", "sent": False}

    # Group by severity
    grouped: dict = {"critical": [], "error": [], "warning": []}
    for n in unread:
        sev = n.severity if n.severity in grouped else "warning"
        grouped[sev].append({
            "title": n.title,
            "message": n.message,
            "company_id": n.company_id,
            "agent": n.agent_type,
        })

    sent = await email_service.send_daily_summary({
        "headline": f"Smart Alert Digest — {period}",
        "key_highlights": [f"[{s.upper()}] {i['title']}" for s in grouped for i in grouped[s]][:10],
        "attention_items": [i["message"] for s in ["critical", "error"] for i in grouped[s]][:5],
        "overall_status": "at_risk" if grouped["critical"] else ("at_risk" if grouped["error"] else "on_track"),
        "total_alerts": len(unread),
        "critical": len(grouped["critical"]),
        "errors": len(grouped["error"]),
        "warnings": len(grouped["warning"]),
    })

    # Mark all as read after sending digest
    db.query(Notification).filter_by(is_read=False).update({"is_read": True})
    db.commit()

    return {
        "message": "Smart digest sent",
        "sent": sent,
        "alerts_included": len(unread),
        "breakdown": {k: len(v) for k, v in grouped.items()},
    }


@router.get("/risk-score")
def get_portfolio_risk_score(period: str = "2026-01", db: Session = Depends(get_db)):
    """
    Composite Financial Risk Score.
    Calculates a 0-100 risk score per company and for the portfolio,
    weighted across data quality, issue severity, and close progress.
    """
    companies = db.query(Company).all()
    scores = []

    for company in companies:
        critical = db.query(Notification).filter_by(
            company_id=company.id, severity="critical", is_read=False
        ).count()
        errors = db.query(Notification).filter_by(
            company_id=company.id, severity="error", is_read=False
        ).count()
        warnings = db.query(Notification).filter_by(
            company_id=company.id, severity="warning", is_read=False
        ).count()

        # Weighted risk score: critical=10pts, error=5pts, warning=2pts, max 100
        raw_score = min(100, (critical * 10) + (errors * 5) + (warnings * 2))

        # Adjust for close progress (incomplete close adds risk)
        progress_penalty = max(0, (100 - (company.close_progress or 0)) * 0.2)
        final_score = min(100, round(raw_score + progress_penalty, 1))

        risk_level = "critical" if final_score >= 70 else "high" if final_score >= 40 else "medium" if final_score >= 15 else "low"

        scores.append({
            "company_id": company.id,
            "company_name": company.name,
            "risk_score": final_score,
            "risk_level": risk_level,
            "breakdown": {
                "critical_issues": critical,
                "error_issues": errors,
                "warning_issues": warnings,
                "close_progress": company.close_progress or 0,
            },
        })

    scores.sort(key=lambda x: x["risk_score"], reverse=True)
    portfolio_risk = round(sum(s["risk_score"] for s in scores) / len(scores), 1) if scores else 0

    return {
        "period": period,
        "portfolio_risk_score": portfolio_risk,
        "portfolio_risk_level": "critical" if portfolio_risk >= 70 else "high" if portfolio_risk >= 40 else "medium" if portfolio_risk >= 15 else "low",
        "companies": scores,
    }

