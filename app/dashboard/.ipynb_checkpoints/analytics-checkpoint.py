"""
Dashboard Analytics Service
RecruitPro CRM
"""

from datetime import date, datetime, timedelta
import pandas as pd
from sqlalchemy import func, and_, case
from database.connection import get_db
from database.models import (
    Candidate, Company, Recruiter, Payment, Notification, User,
    CandidateStatus, PaymentStatus
)


def get_dashboard_kpis() -> dict:
    """Get all KPI metrics for the dashboard."""
    today = date.today()
    month_start = today.replace(day=1)
    last_month_start = (month_start - timedelta(days=1)).replace(day=1)

    with get_db() as db:
        # Core counts
        total = db.query(Candidate).count()
        active = db.query(Candidate).filter(
            Candidate.status.in_([
                CandidateStatus.INTERVIEW_SCHEDULED,
                CandidateStatus.SELECTED,
            ])
        ).count()
        joined = db.query(Candidate).filter(
            Candidate.status.in_([
                CandidateStatus.JOINED,
                CandidateStatus.COMPLETED_30,
                CandidateStatus.COMPLETED_60,
                CandidateStatus.COMPLETED_90,
                CandidateStatus.PAYMENT_PENDING,
                CandidateStatus.PAYMENT_RECEIVED,
            ])
        ).count()
        completed_90 = db.query(Candidate).filter(
            Candidate.status.in_([
                CandidateStatus.COMPLETED_90,
                CandidateStatus.PAYMENT_PENDING,
            ])
        ).count()
        drops = db.query(Candidate).filter(
            Candidate.status == CandidateStatus.DROP
        ).count()

        # Payment KPIs
        pending_payment = db.query(func.sum(Candidate.payment_amount)).filter(
            Candidate.payment_status == PaymentStatus.PENDING,
            Candidate.is_90_day_eligible == True,
        ).scalar() or 0

        received_payment = db.query(func.sum(Candidate.payment_amount)).filter(
            Candidate.payment_status == PaymentStatus.RECEIVED,
        ).scalar() or 0

        # This month
        month_joins = db.query(Candidate).filter(
            Candidate.joining_date >= month_start
        ).count()
        month_revenue = db.query(func.sum(Candidate.payment_amount)).filter(
            Candidate.payment_received_date >= month_start,
            Candidate.payment_status == PaymentStatus.RECEIVED
        ).scalar() or 0

        # Notifications
        unread_notifications = db.query(Notification).filter(
            Notification.is_read == False
        ).count()

        # Pipeline eligibility alerts
        alerts_90_day = db.query(Candidate).filter(
            Candidate.is_90_day_eligible == True,
            Candidate.payment_status == PaymentStatus.PENDING
        ).count()

        return {
            "total_candidates": total,
            "active_candidates": active,
            "joined_candidates": joined,
            "completed_90_days": completed_90,
            "drops": drops,
            "pending_payment": pending_payment,
            "received_payment": received_payment,
            "month_joins": month_joins,
            "month_revenue": month_revenue,
            "unread_notifications": unread_notifications,
            "alerts_90_day": alerts_90_day,
        }


def get_monthly_trend(months: int = 12) -> pd.DataFrame:
    """Get monthly joining and payment trend."""
    today = date.today()
    records = []

    with get_db() as db:
        for i in range(months - 1, -1, -1):
            ref = (today.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
            if i == 0:
                month_end = today
            else:
                next_month = (ref + timedelta(days=32)).replace(day=1)
                month_end = next_month - timedelta(days=1)

            joins = db.query(Candidate).filter(
                Candidate.joining_date >= ref,
                Candidate.joining_date <= month_end,
            ).count()

            revenue = db.query(func.sum(Candidate.payment_amount)).filter(
                Candidate.payment_received_date >= ref,
                Candidate.payment_received_date <= month_end,
                Candidate.payment_status == PaymentStatus.RECEIVED,
            ).scalar() or 0

            records.append({
                "month": ref.strftime("%b %Y"),
                "joins": joins,
                "revenue": revenue,
            })

    return pd.DataFrame(records)


def get_status_distribution() -> pd.DataFrame:
    """Get candidate count by status."""
    with get_db() as db:
        results = (
            db.query(Candidate.status, func.count(Candidate.id).label("count"))
            .group_by(Candidate.status)
            .all()
        )
        return pd.DataFrame([{"status": r.status.value, "count": r.count} for r in results])


def get_company_pipeline() -> pd.DataFrame:
    """Get candidate count and pending revenue by company."""
    with get_db() as db:
        results = (
            db.query(
                Company.name,
                func.count(Candidate.id).label("total_candidates"),
                func.sum(
                    case(
                        (Candidate.status == CandidateStatus.JOINED, 1),
                        else_=0
                    )
                ).label("joined"),
                func.sum(
                    case(
                        (Candidate.payment_status == PaymentStatus.PENDING, Candidate.payment_amount),
                        else_=0
                    )
                ).label("pending_amount"),
                func.sum(
                    case(
                        (Candidate.payment_status == PaymentStatus.RECEIVED, Candidate.payment_amount),
                        else_=0
                    )
                ).label("received_amount"),
            )
            .join(Company, Candidate.company_id == Company.id)
            .group_by(Company.id, Company.name)
            .order_by(func.count(Candidate.id).desc())
            .limit(10)
            .all()
        )

        return pd.DataFrame([{
            "company": r.name,
            "total_candidates": r.total_candidates,
            "joined": r.joined or 0,
            "pending_amount": float(r.pending_amount or 0),
            "received_amount": float(r.received_amount or 0),
        } for r in results])


def get_recruiter_performance() -> pd.DataFrame:
    """Get performance metrics per recruiter."""
    with get_db() as db:
        results = (
            db.query(
                User.full_name,
                func.count(Candidate.id).label("total"),
                func.sum(case((Candidate.status == CandidateStatus.JOINED, 1), else_=0)).label("joins"),
                func.sum(case((Candidate.status == CandidateStatus.DROP, 1), else_=0)).label("drops"),
                func.sum(case(
                    (Candidate.payment_status == PaymentStatus.RECEIVED, Candidate.payment_amount),
                    else_=0
                )).label("revenue"),
            )
            .join(Recruiter, Candidate.recruiter_id == Recruiter.id)
            .join(User, Recruiter.user_id == User.id)
            .group_by(User.id, User.full_name)
            .order_by(func.count(Candidate.id).desc())
            .all()
        )

        return pd.DataFrame([{
            "recruiter": r.full_name,
            "total": r.total,
            "joins": r.joins or 0,
            "drops": r.drops or 0,
            "revenue": float(r.revenue or 0),
        } for r in results])


def get_upcoming_90day_alerts(days_ahead: int = 15) -> list:
    """Candidates approaching 90-day mark."""
    today = date.today()
    threshold = today - timedelta(days=75)  # joined 75+ days ago

    with get_db() as db:
        candidates = (
            db.query(Candidate, Company.name.label("company_name"))
            .outerjoin(Company, Candidate.company_id == Company.id)
            .filter(
                Candidate.joining_date <= threshold,
                Candidate.joining_date >= today - timedelta(days=89),
                Candidate.status.in_([
                    CandidateStatus.JOINED,
                    CandidateStatus.COMPLETED_30,
                    CandidateStatus.COMPLETED_60,
                ])
            )
            .order_by(Candidate.joining_date)
            .all()
        )

        alerts = []
        for row in candidates:
            c = row.Candidate
            days_in = (today - c.joining_date).days
            days_left = 90 - days_in
            alerts.append({
                "id": c.id,
                "candidate_id": c.candidate_id,
                "name": c.name,
                "phone": c.phone,
                "company": row.company_name or "—",
                "joining_date": c.joining_date,
                "days_in": days_in,
                "days_left": days_left,
                "payment_amount": c.payment_amount or 0,
            })

        return alerts


def get_unread_notifications(user_id: int, limit: int = 20) -> list:
    with get_db() as db:
        notifs = (
            db.query(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .all()
        )
        return [{
            "id": n.id,
            "type": n.type.value,
            "title": n.title,
            "message": n.message,
            "is_read": n.is_read,
            "created_at": n.created_at,
            "candidate_id": n.candidate_id,
        } for n in notifs]


def mark_notification_read(notification_id: int):
    with get_db() as db:
        notif = db.query(Notification).filter(Notification.id == notification_id).first()
        if notif:
            notif.is_read = True


def mark_all_notifications_read(user_id: int):
    with get_db() as db:
        db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).update({"is_read": True})
