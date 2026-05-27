import sys
sys.path.insert(0, r'C:\Users\Vansh\Documents\recruitment_crm')

from database.connection import get_db
from database.models import Candidate, Notification, User, NotificationType
from datetime import date

with get_db() as db:
    # Get all 90-day eligible candidates
    eligible = db.query(Candidate).filter(
        Candidate.is_90_day_eligible == True
    ).all()

    # Get all admin users
    admins = db.query(User).filter(User.is_active == True).all()

    count = 0
    for c in eligible:
        days = (date.today() - c.joining_date).days if c.joining_date else 0
        for admin in admins:
            # Check if notification already exists
            existing = db.query(Notification).filter(
                Notification.candidate_id == c.id,
                Notification.type == NotificationType.DAY_90,
                Notification.user_id == admin.id,
            ).first()

            if not existing:
                notif = Notification(
                    user_id=admin.id,
                    candidate_id=c.id,
                    type=NotificationType.DAY_90,
                    title=f"90 Days Complete: {c.name}",
                    message=f"{c.name} has completed {days} days at the company. Please follow up with the company to collect payment.",
                    is_read=False,
                )
                db.add(notif)
                count += 1

    db.commit()
    print(f"Created {count} new notifications for {len(eligible)} eligible candidates!")