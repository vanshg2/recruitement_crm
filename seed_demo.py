"""
Demo Data Seeder
Populates the database with realistic sample data for testing.
Run: python seed_demo.py
RecruitPro CRM
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from datetime import date, timedelta
import random
import bcrypt
from database.connection import init_database, get_db
from database.models import (
    User, Recruiter, Company, Candidate, Notification,
    UserRole, CandidateStatus, PaymentStatus, NotificationType
)

COMPANIES = [
    ("TechCorp Solutions", "IT/Software", "Rahul Sharma", "rahul@techcorp.com", "9811111111"),
    ("FinServ India", "Banking/Finance", "Priya Mehta", "priya@finserv.com", "9822222222"),
    ("MediCare Hospitals", "Healthcare", "Dr. Suresh Kumar", "suresh@medicare.com", "9833333333"),
    ("Infinity Logistics", "Logistics", "Arun Verma", "arun@infinity.com", "9844444444"),
    ("EduTech Academy", "Education", "Smita Joshi", "smita@edutech.com", "9855555555"),
]

RECRUITERS = [
    ("Neha Gupta", "neha", "neha@recruitpro.com", "IT Recruitment", "Tech Hiring", 12),
    ("Amit Sharma", "amit", "amit@recruitpro.com", "Finance Recruitment", "BFSI", 10),
    ("Pooja Rao", "pooja", "pooja@recruitpro.com", "Healthcare Recruitment", "Medical Staffing", 8),
]

CANDIDATES = [
    ("Arjun Mehta", "9900010001", "arjun@gmail.com", "Software Engineer", 800000, -95, "joined"),
    ("Divya Sharma", "9900010002", "divya@gmail.com", "Business Analyst", 600000, -92, "joined"),
    ("Rahul Singh", "9900010003", "rahul@gmail.com", "Data Analyst", 700000, -65, "joined"),
    ("Priya Nair", "9900010004", "priya@gmail.com", "HR Manager", 750000, -45, "joined"),
    ("Vikram Patel", "9900010005", "vikram@gmail.com", "Project Manager", 1200000, -30, "joined"),
    ("Sneha Joshi", "9900010006", "sneha@gmail.com", "QA Engineer", 650000, -10, "joined"),
    ("Karan Malhotra", "9900010007", "karan@gmail.com", "Sales Executive", 500000, 0, "selected"),
    ("Ritu Verma", "9900010008", "ritu@gmail.com", "Content Writer", 400000, 0, "selected"),
    ("Sunil Kumar", "9900010009", "sunil@gmail.com", "Network Engineer", 900000, -100, "received"),
    ("Kavya Reddy", "9900010010", "kavya@gmail.com", "UX Designer", 850000, -110, "received"),
    ("Aditya Gupta", "9900010011", "aditya@gmail.com", "DevOps Engineer", 1100000, -5, "interview"),
    ("Meena Pillai", "9900010012", "meena@gmail.com", "Accountant", 550000, 0, "drop"),
    ("Rohit Jain", "9900010013", "rohit@gmail.com", "Marketing Manager", 950000, -85, "joined"),
    ("Sunita Agarwal", "9900010014", "sunita@gmail.com", "Operations Head", 1300000, -92, "joined"),
    ("Deepak Choudhary", "9900010015", "deepak@gmail.com", "Product Manager", 1500000, -95, "joined"),
]


def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def seed():
    print("🌱 Initializing database...")
    init_database()

    with get_db() as db:
        print("🏢 Seeding companies...")
        company_ids = {}
        for name, industry, contact, email, phone in COMPANIES:
            existing = db.query(Company).filter(Company.name == name).first()
            if not existing:
                c = Company(name=name, industry=industry, contact_person=contact,
                            contact_email=email, contact_phone=phone)
                db.add(c)
                db.flush()
                company_ids[name] = c.id
            else:
                company_ids[name] = existing.id
        db.flush()

        print("👤 Seeding recruiters...")
        recruiter_ids = []
        for full_name, username, email, dept, spec, target in RECRUITERS:
            existing_user = db.query(User).filter(User.username == username).first()
            if not existing_user:
                user = User(
                    username=username, email=email,
                    password_hash=hash_pw("recruiter@123"),
                    full_name=full_name, role=UserRole.RECRUITER,
                    is_active=True,
                )
                db.add(user)
                db.flush()
                rec = Recruiter(
                    user_id=user.id,
                    employee_id=f"EMP{str(user.id).zfill(4)}",
                    department=dept, specialization=spec,
                    target_monthly=target,
                    joining_date=date.today() - timedelta(days=365),
                )
                db.add(rec)
                db.flush()
                recruiter_ids.append(rec.id)
            else:
                if existing_user.recruiter_profile:
                    recruiter_ids.append(existing_user.recruiter_profile.id)

        db.flush()
        company_list = list(company_ids.values())

        print("👥 Seeding candidates...")
        cand_counter = db.query(Candidate).count()
        for name, phone, email, desig, ctc, days_offset, scenario in CANDIDATES:
            existing = db.query(Candidate).filter(Candidate.phone == phone).first()
            if existing:
                continue

            cand_counter += 1
            cid = f"CND{str(cand_counter + 1000).zfill(5)}"
            company_id = random.choice(company_list)
            recruiter_id = random.choice(recruiter_ids) if recruiter_ids else None
            payment_amount = round(ctc * 0.0833, -3)  # ~1 month salary

            # Dates
            today = date.today()
            joining_date = None
            selection_date = today + timedelta(days=days_offset - 10) if days_offset < 0 else None

            # Scenario mapping
            status = CandidateStatus.SELECTED
            payment_status = PaymentStatus.PENDING
            payment_received_date = None
            is_eligible = False
            days_completed = 0

            if scenario == "interview":
                status = CandidateStatus.INTERVIEW_SCHEDULED
            elif scenario == "selected":
                status = CandidateStatus.SELECTED
                selection_date = today - timedelta(days=5)
            elif scenario == "drop":
                status = CandidateStatus.DROP
                selection_date = today - timedelta(days=30)
            elif scenario == "joined":
                joining_date = today + timedelta(days=days_offset)
                days_completed = abs(days_offset)
                if days_completed >= 90:
                    status = CandidateStatus.COMPLETED_90
                    is_eligible = True
                    payment_status = PaymentStatus.PENDING
                elif days_completed >= 60:
                    status = CandidateStatus.COMPLETED_60
                elif days_completed >= 30:
                    status = CandidateStatus.COMPLETED_30
                else:
                    status = CandidateStatus.JOINED
            elif scenario == "received":
                joining_date = today + timedelta(days=days_offset)
                days_completed = abs(days_offset)
                status = CandidateStatus.PAYMENT_RECEIVED
                payment_status = PaymentStatus.RECEIVED
                is_eligible = True
                payment_received_date = today - timedelta(days=random.randint(1, 15))

            cand = Candidate(
                candidate_id=cid,
                name=name, phone=phone, email=email,
                company_id=company_id, recruiter_id=recruiter_id,
                designation=desig, ctc=ctc,
                selection_date=selection_date,
                joining_date=joining_date,
                status=status,
                payment_status=payment_status,
                payment_amount=payment_amount,
                payment_received_date=payment_received_date,
                is_90_day_eligible=is_eligible,
                days_completed=days_completed,
                notes=f"Demo candidate - {scenario} scenario",
            )
            db.add(cand)

        db.flush()

        print("🔔 Creating sample notifications...")
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            eligible_cands = db.query(Candidate).filter(
                Candidate.is_90_day_eligible == True,
                Candidate.payment_status == PaymentStatus.PENDING
            ).limit(3).all()
            for c in eligible_cands:
                db.add(Notification(
                    user_id=admin.id,
                    candidate_id=c.id,
                    type=NotificationType.DAY_90,
                    title=f"🎯 90 Days Complete: {c.name}",
                    message=f"{c.name} has completed 90 days. Please initiate payment follow-up.",
                    is_read=False,
                ))

        db.commit()
        print("\n✅ Demo data seeded successfully!")
        print("─" * 40)
        print("🔐 Login Credentials:")
        print("   Admin:     admin / admin@123")
        for full_name, username, *_ in RECRUITERS:
            print(f"   {full_name[:15]}: {username} / recruiter@123")
        print("─" * 40)
        print("🚀 Run: streamlit run app.py")


if __name__ == "__main__":
    seed()
