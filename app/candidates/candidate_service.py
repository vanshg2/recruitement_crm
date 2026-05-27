"""
Candidate Management - Business Logic
RecruitPro CRM
"""

import uuid
from datetime import date, datetime, timedelta
from typing import Optional, List
import pandas as pd
from sqlalchemy import and_, or_, func
from database.connection import get_db
import streamlit as st
from database.models import (
    Candidate, Company, Recruiter, CandidateTimeline, ActivityLog,
    Notification, CandidateStatus, PaymentStatus, NotificationType, User
)


# ─────────────────────────────────────────────────
# ID GENERATION
# ─────────────────────────────────────────────────

def generate_candidate_id() -> str:
    with get_db() as db:
        count = db.query(Candidate).count()
        return f"CND{str(count + 1001).zfill(5)}"


# ─────────────────────────────────────────────────
# CRUD OPERATIONS
# ─────────────────────────────────────────────────

def create_candidate(data: dict, performed_by: str = "System") -> tuple[bool, str, Optional[int]]:
    try:
        with get_db() as db:
            candidate = Candidate(
                candidate_id=generate_candidate_id(),
                name=data["name"],
                phone=data["phone"],
                alternate_phone=data.get("alternate_phone", ""),
                email=data.get("email", ""),
                company_id=data.get("company_id"),
                recruiter_id=data.get("recruiter_id"),
                designation=data.get("designation", ""),
                ctc=data.get("ctc", 0),
                selection_date=data.get("selection_date"),
                joining_date=data.get("joining_date"),
                expected_joining_date=data.get("expected_joining_date"),
                status=CandidateStatus(data.get("status", CandidateStatus.SELECTED.value)),
                payment_amount=data.get("payment_amount", 0),
                notes=data.get("notes", ""),
            )
            db.add(candidate)
            db.flush()

            # Add timeline entry
            timeline = CandidateTimeline(
                candidate_id=candidate.id,
                event_type="CREATED",
                title="Candidate Added",
                description=f"Candidate {candidate.name} was added to the system",
                performed_by=performed_by,
            )
            db.add(timeline)

            # Log activity
            log = ActivityLog(
                action="CREATE_CANDIDATE",
                entity_type="candidate",
                entity_id=candidate.id,
                details=f"Created candidate {candidate.candidate_id}: {candidate.name}",
            )
            db.add(log)

            cid = candidate.id
            return True, f"Candidate {candidate.candidate_id} created successfully", cid

    except Exception as e:
        return False, str(e), None


def update_candidate(candidate_id: int, data: dict, performed_by: str = "System") -> tuple[bool, str]:
    try:
        with get_db() as db:
            candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
            if not candidate:
                return False, "Candidate not found"

            old_status = candidate.status.value
            old_payment_status = candidate.payment_status.value if candidate.payment_status else None

            # Update fields
            updateable = [
                "name", "phone", "alternate_phone", "email", "company_id",
                "recruiter_id", "designation", "ctc", "selection_date",
                "joining_date", "expected_joining_date", "payment_amount",
                "payment_received_date", "invoice_number", "invoice_date",
                "drop_reason", "notes", "resume_path"
            ]
            for field in updateable:
                if field in data:
                    setattr(candidate, field, data[field])

            # Handle status change
            if "status" in data:
                new_status = CandidateStatus(data["status"])
                if new_status != candidate.status:
                    candidate.status = new_status
                    _add_timeline_event(
                        db, candidate_id,
                        "STATUS_CHANGE",
                        f"Status Updated: {old_status} → {new_status.value}",
                        f"Status changed from {old_status} to {new_status.value}",
                        performed_by
                    )

            # Handle payment status change
            if "payment_status" in data:
                new_ps = PaymentStatus(data["payment_status"])
                if candidate.payment_status != new_ps:
                    candidate.payment_status = new_ps
                    _add_timeline_event(
                        db, candidate_id,
                        "PAYMENT_UPDATE",
                        f"Payment Status: {new_ps.value}",
                        f"Payment status updated to {new_ps.value}",
                        performed_by
                    )

            return True, "Candidate updated successfully"
    except Exception as e:
        return False, str(e)


def delete_candidate(candidate_id: int) -> tuple[bool, str]:
    try:
        with get_db() as db:
            candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
            if not candidate:
                return False, "Candidate not found"
            candidate_name = candidate.name
            db.delete(candidate)
            return True, f"Candidate {candidate_name} deleted successfully"
    except Exception as e:
        return False, str(e)


def get_candidate(candidate_id: int) -> Optional[Candidate]:
    with get_db() as db:
        return db.query(Candidate).filter(Candidate.id == candidate_id).first()


def get_all_candidates(
    search: str = "",
    status_filter: str = "",
    company_id: int = None,
    recruiter_id: int = None,
    payment_status: str = "",
    date_from: date = None,
    date_to: date = None,
    limit: int = 500,
    offset: int = 0,
) -> List[dict]:
    with get_db() as db:
        query = (
            db.query(
                Candidate,
                Company.name.label("company_name"),
                User.full_name.label("recruiter_name"),
            )
            .outerjoin(Company, Candidate.company_id == Company.id)
            .outerjoin(Recruiter, Candidate.recruiter_id == Recruiter.id)
            .outerjoin(User, Recruiter.user_id == User.id)
        )

        # Recruiters see all candidates but without financial data (handled in UI)

        # Search filter
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Candidate.name.ilike(search_term),
                    Candidate.phone.ilike(search_term),
                    Candidate.email.ilike(search_term),
                    Candidate.candidate_id.ilike(search_term),
                    Company.name.ilike(search_term),
                )
            )

        if status_filter:
            query = query.filter(Candidate.status == CandidateStatus(status_filter))
        if company_id:
            query = query.filter(Candidate.company_id == company_id)
        if recruiter_id:
            query = query.filter(Candidate.recruiter_id == recruiter_id)
        if payment_status:
            query = query.filter(Candidate.payment_status == PaymentStatus(payment_status))
        if date_from:
            query = query.filter(Candidate.joining_date >= date_from)
        if date_to:
            query = query.filter(Candidate.joining_date <= date_to)

        results = query.order_by(Candidate.created_at.desc()).limit(limit).offset(offset).all()

        candidates = []
        for row in results:
            c = row.Candidate
            days = 0
            if c.joining_date:
                days = (date.today() - c.joining_date).days

            candidates.append({
                "id": c.id,
                "candidate_id": c.candidate_id,
                "name": c.name,
                "phone": c.phone if c.phone != "0000000000" else "—",
                "email": c.email or "",
                "company_name": row.company_name or "—",
                "recruiter_name": row.recruiter_name or "—",
                "designation": c.designation or "",
                "status": c.status.value,
                "payment_status": c.payment_status.value if c.payment_status else "Pending",
                "payment_amount": c.payment_amount or 0,
                "selection_date": c.selection_date,
                "joining_date": c.joining_date,
                "days_since_joining": days,
                "is_90_day_eligible": c.is_90_day_eligible,
                "notes": c.notes or "",
                "created_at": c.created_at,
            })

        return candidates


def get_candidates_dataframe(**kwargs) -> pd.DataFrame:
    candidates = get_all_candidates(**kwargs)
    if not candidates:
        return pd.DataFrame()
    return pd.DataFrame(candidates)


# ─────────────────────────────────────────────────
# 90-DAY TRACKING
# ─────────────────────────────────────────────────

def update_candidate_day_tracking() -> int:
    """
    Background job: recalculate days for joined candidates,
    update statuses and create notifications.
    Returns count of updated candidates.
    """
    updated = 0
    today = date.today()

    try:
        with get_db() as db:
            joined_candidates = db.query(Candidate).filter(
                Candidate.joining_date.isnot(None),
                Candidate.status.in_([
                    CandidateStatus.JOINED,
                    CandidateStatus.COMPLETED_30,
                    CandidateStatus.COMPLETED_60,
                    CandidateStatus.COMPLETED_90,
                    CandidateStatus.PAYMENT_PENDING,
                ])
            ).all()

            for candidate in joined_candidates:
                days = (today - candidate.joining_date).days
                candidate.days_completed = days

                old_status = candidate.status

                if days >= 90 and old_status not in [
                    CandidateStatus.COMPLETED_90,
                    CandidateStatus.PAYMENT_PENDING,
                    CandidateStatus.PAYMENT_RECEIVED
                ]:
                    candidate.status = CandidateStatus.COMPLETED_90
                    candidate.is_90_day_eligible = True
                    _notify_all_admins(
                        db, candidate,
                        NotificationType.DAY_90,
                        f"🎯 90 Days Complete: {candidate.name}",
                        f"{candidate.name} has completed 90 days at company. Initiate payment follow-up."
                    )
                    updated += 1

                elif days >= 60 and old_status == CandidateStatus.COMPLETED_30:
                    candidate.status = CandidateStatus.COMPLETED_60
                    _notify_all_admins(
                        db, candidate,
                        NotificationType.DAY_60,
                        f"⏱ 60 Days: {candidate.name}",
                        f"{candidate.name} has completed 60 days. 30 more days to payment milestone."
                    )
                    updated += 1

                elif days >= 30 and old_status == CandidateStatus.JOINED:
                    candidate.status = CandidateStatus.COMPLETED_30
                    _notify_all_admins(
                        db, candidate,
                        NotificationType.DAY_30,
                        f"📅 30 Days: {candidate.name}",
                        f"{candidate.name} has completed 30 days at company."
                    )
                    updated += 1

            db.commit()

    except Exception as e:
        print(f"Error in day tracking: {e}")

    return updated


def _notify_all_admins(db, candidate, notif_type, title, message):
    """Create notifications for all admin/manager users."""
    admins = db.query(User).filter(
        User.role.in_(["admin", "manager"]),
        User.is_active == True
    ).all()
    for admin in admins:
        notif = Notification(
            user_id=admin.id,
            candidate_id=candidate.id,
            type=notif_type,
            title=title,
            message=message,
        )
        db.add(notif)


def _add_timeline_event(db, candidate_id, event_type, title, description, performed_by):
    timeline = CandidateTimeline(
        candidate_id=candidate_id,
        event_type=event_type,
        title=title,
        description=description,
        performed_by=performed_by,
    )
    db.add(timeline)


# ─────────────────────────────────────────────────
# BULK IMPORT
# ─────────────────────────────────────────────────

def bulk_import_candidates(df: pd.DataFrame, recruiter_id: int) -> tuple[int, int, list]:
    """Import candidates from DataFrame. Returns (success, failed, errors)."""
    success = 0
    failed = 0
    errors = []

    with get_db() as db:
        companies_cache = {c.name: c.id for c in db.query(Company).all()}

    for idx, row in df.iterrows():
        try:
            company_id = companies_cache.get(str(row.get("Company", "")))
            data = {
                "name": str(row.get("Name", "")).strip(),
                "phone": str(row.get("Phone", "")).strip(),
                "email": str(row.get("Email", "")).strip(),
                "designation": str(row.get("Designation", "")).strip(),
                "company_id": company_id,
                "recruiter_id": recruiter_id,
                "ctc": float(row.get("CTC", 0) or 0),
                "payment_amount": float(row.get("Payment Amount", 0) or 0),
                "notes": str(row.get("Notes", "")).strip(),
                "status": CandidateStatus.SELECTED.value,
            }
            if not data["name"] or not data["phone"]:
                errors.append(f"Row {idx+2}: Name and Phone are required")
                failed += 1
                continue

            ok, msg, _ = create_candidate(data, "Bulk Import")
            if ok:
                success += 1
            else:
                errors.append(f"Row {idx+2}: {msg}")
                failed += 1
        except Exception as e:
            errors.append(f"Row {idx+2}: {str(e)}")
            failed += 1

    return success, failed, errors


def export_candidates_excel(candidates: list) -> bytes:
    """Export candidates list to Excel bytes."""
    if not candidates:
        return b""
    df = pd.DataFrame(candidates)
    export_cols = [
        "candidate_id", "name", "phone", "email", "company_name",
        "recruiter_name", "designation", "status", "payment_status",
        "payment_amount", "selection_date", "joining_date", "days_since_joining"
    ]
    available = [c for c in export_cols if c in df.columns]
    df = df[available]
    df.columns = [c.replace("_", " ").title() for c in available]

    from io import BytesIO
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Candidates")
    return buf.getvalue()