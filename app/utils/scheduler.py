"""
Background Scheduler - APScheduler
Handles 90-day tracking automation
RecruitPro CRM
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import streamlit as st

logger = logging.getLogger(__name__)

_scheduler = None


def _job_update_day_tracking():
    """APScheduler job: update all candidate day tracking."""
    try:
        from app.candidates.candidate_service import update_candidate_day_tracking
        count = update_candidate_day_tracking()
        logger.info(f"[Scheduler] Day tracking updated for {count} candidates")
    except Exception as e:
        logger.error(f"[Scheduler] Day tracking failed: {e}")


def _job_check_overdue_payments():
    """APScheduler job: mark overdue payments."""
    try:
        from datetime import date, timedelta
        from database.connection import get_db
        from database.models import Candidate, PaymentStatus, CandidateStatus, Notification, User

        today = date.today()
        overdue_threshold = today - timedelta(days=105)  # 90 days + 15 grace

        with get_db() as db:
            overdue = db.query(Candidate).filter(
                Candidate.joining_date <= overdue_threshold,
                Candidate.payment_status == PaymentStatus.PENDING,
                Candidate.is_90_day_eligible == True,
            ).all()

            for c in overdue:
                c.payment_status = PaymentStatus.OVERDUE
                admins = db.query(User).filter(User.role.in_(["admin", "manager"])).all()
                for admin in admins:
                    existing = db.query(Notification).filter(
                        Notification.candidate_id == c.id,
                        Notification.type == "payment_overdue",
                        Notification.is_read == False,
                    ).first()
                    if not existing:
                        db.add(Notification(
                            user_id=admin.id,
                            candidate_id=c.id,
                            type="payment_overdue",
                            title=f"⚠️ Overdue Payment: {c.name}",
                            message=f"Payment from {c.name}'s company is overdue. Immediate follow-up required.",
                        ))

            if overdue:
                logger.info(f"[Scheduler] Marked {len(overdue)} candidates as payment overdue")

    except Exception as e:
        logger.error(f"[Scheduler] Overdue payment check failed: {e}")


def _scheduler_listener(event):
    if event.exception:
        logger.error(f"[Scheduler] Job {event.job_id} failed: {event.exception}")
    else:
        logger.debug(f"[Scheduler] Job {event.job_id} executed successfully")


def start_scheduler():
    """Initialize and start the background scheduler."""
    global _scheduler

    if _scheduler and _scheduler.running:
        return _scheduler

    _scheduler = BackgroundScheduler(
        timezone="Asia/Kolkata",
        job_defaults={"coalesce": True, "max_instances": 1}
    )

    # Run day tracking every hour
    _scheduler.add_job(
        _job_update_day_tracking,
        trigger=CronTrigger(minute=0),  # Top of every hour
        id="day_tracking",
        name="Candidate Day Tracking",
        replace_existing=True,
    )

    # Check overdue payments at 9 AM daily
    _scheduler.add_job(
        _job_check_overdue_payments,
        trigger=CronTrigger(hour=9, minute=0),
        id="overdue_payment_check",
        name="Overdue Payment Check",
        replace_existing=True,
    )

    _scheduler.add_listener(_scheduler_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    _scheduler.start()

    logger.info("[Scheduler] Background scheduler started")
    return _scheduler


def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("[Scheduler] Background scheduler stopped")


def get_scheduler_status() -> dict:
    global _scheduler
    if not _scheduler:
        return {"running": False, "jobs": []}

    jobs = []
    for job in _scheduler.get_jobs():
        next_run = job.next_run_time
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": next_run.strftime("%Y-%m-%d %H:%M:%S") if next_run else "N/A",
        })

    return {"running": _scheduler.running, "jobs": jobs}


def run_day_tracking_now():
    """Manually trigger day tracking (for testing/admin use)."""
    _job_update_day_tracking()
    _job_check_overdue_payments()
