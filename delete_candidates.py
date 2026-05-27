import sys
sys.path.insert(0, r'C:\Users\Vansh\Documents\recruitment_crm')

from database.connection import get_db
from database.models import User, Recruiter, Candidate, CandidateTimeline, ActivityLog, Notification, Company

with get_db() as db:
    # ── Delete all candidates and related data ──
    db.query(Notification).filter(Notification.candidate_id != None).delete(synchronize_session=False)
    db.query(CandidateTimeline).delete(synchronize_session=False)
    db.query(ActivityLog).filter(ActivityLog.candidate_id != None).delete(synchronize_session=False)
    count = db.query(Candidate).count()
    db.query(Candidate).delete(synchronize_session=False)
    print(f"✅ Deleted {count} candidates")

    # ── Delete sample recruiters ──
    sample_usernames = ['neha', 'amit', 'pooja']
    for username in sample_usernames:
        user = db.query(User).filter(User.username == username).first()
        if user:
            rec = db.query(Recruiter).filter(Recruiter.user_id == user.id).first()
            if rec:
                db.delete(rec)
            db.delete(user)
            print(f"✅ Deleted recruiter: {username}")

    # ── Delete sample companies ──
    sample_companies = ['TechCorp Solutions', 'FinServ India', 'MediCare Hospitals']
    for name in sample_companies:
        comp = db.query(Company).filter(Company.name == name).first()
        if comp:
            db.delete(comp)
            print(f"✅ Deleted company: {name}")

    db.commit()
    print("\n🎉 All sample data cleared successfully!")