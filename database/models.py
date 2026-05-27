"""
Database Models - SQLAlchemy ORM
RecruitPro CRM
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Date, DateTime, Float,
    Boolean, ForeignKey, Enum, Index, create_engine
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()


# ─────────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    RECRUITER = "recruiter"
    MANAGER = "manager"


class CandidateStatus(str, enum.Enum):
    INTERVIEW_SCHEDULED = "Interview Scheduled"
    SELECTED = "Selected"
    JOINED = "Joined"
    DROP = "Drop"
    COMPLETED_30 = "Completed 30 Days"
    COMPLETED_60 = "Completed 60 Days"
    COMPLETED_90 = "Completed 90 Days"
    PAYMENT_PENDING = "Payment Pending"
    PAYMENT_RECEIVED = "Payment Received"


class PaymentStatus(str, enum.Enum):
    PENDING = "Pending"
    INVOICED = "Invoiced"
    RECEIVED = "Received"
    OVERDUE = "Overdue"


class NotificationType(str, enum.Enum):
    DAY_30 = "30_days"
    DAY_60 = "60_days"
    DAY_90 = "90_days"
    PAYMENT_DUE = "payment_due"
    PAYMENT_OVERDUE = "payment_overdue"
    GENERAL = "general"


# ─────────────────────────────────────────────────
# MODELS
# ─────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.RECRUITER, nullable=False)
    phone = Column(String(20))
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    recruiter_profile = relationship("Recruiter", back_populates="user", uselist=False)
    activity_logs = relationship("ActivityLog", back_populates="user")
    notifications = relationship("Notification", back_populates="user")

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False, index=True)
    industry = Column(String(100))
    contact_person = Column(String(100))
    contact_email = Column(String(100))
    contact_phone = Column(String(20))
    address = Column(Text)
    website = Column(String(200))
    payment_terms_days = Column(Integer, default=90)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    candidates = relationship("Candidate", back_populates="company")
    payments = relationship("Payment", back_populates="company")

    def __repr__(self):
        return f"<Company {self.name}>"


class Recruiter(Base):
    __tablename__ = "recruiters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    employee_id = Column(String(20), unique=True)
    department = Column(String(100))
    specialization = Column(String(200))
    target_monthly = Column(Integer, default=0)
    joining_date = Column(Date)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    user = relationship("User", back_populates="recruiter_profile")
    candidates = relationship("Candidate", back_populates="recruiter")

    def __repr__(self):
        return f"<Recruiter {self.user.full_name if self.user else self.id}>"


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    phone = Column(String(20), nullable=False, index=True)
    alternate_phone = Column(String(20))
    email = Column(String(100), index=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    recruiter_id = Column(Integer, ForeignKey("recruiters.id"))
    designation = Column(String(100))
    ctc = Column(Float)

    # Dates
    selection_date = Column(Date)
    joining_date = Column(Date, index=True)
    expected_joining_date = Column(Date)

    # Status
    status = Column(
        Enum(CandidateStatus),
        default=CandidateStatus.SELECTED,
        nullable=False,
        index=True
    )

    # Payment
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    payment_amount = Column(Float, default=0.0)
    payment_received_date = Column(Date)
    invoice_number = Column(String(50))
    invoice_date = Column(Date)

    # Tracking
    days_completed = Column(Integer, default=0)
    is_90_day_eligible = Column(Boolean, default=False)
    drop_reason = Column(Text)
    resume_path = Column(String(500))
    notes = Column(Text)

    # Meta
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    company = relationship("Company", back_populates="candidates")
    recruiter = relationship("Recruiter", back_populates="candidates")
    payments = relationship("Payment", back_populates="candidate")
    notifications = relationship("Notification", back_populates="candidate")
    timeline = relationship("CandidateTimeline", back_populates="candidate", order_by="CandidateTimeline.event_date")
    activity_logs = relationship("ActivityLog", back_populates="candidate")

    # Indexes
    __table_args__ = (
        Index("idx_candidate_status_payment", "status", "payment_status"),
        Index("idx_candidate_joining", "joining_date", "is_90_day_eligible"),
    )

    def __repr__(self):
        return f"<Candidate {self.candidate_id}: {self.name}>"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    payment_ref = Column(String(50), unique=True, nullable=False)
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    company_id = Column(Integer, ForeignKey("companies.id"))
    amount = Column(Float, nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    due_date = Column(Date)
    received_date = Column(Date)
    invoice_number = Column(String(50))
    invoice_date = Column(Date)
    payment_mode = Column(String(50))  # Bank Transfer, Cheque, etc.
    transaction_id = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    candidate = relationship("Candidate", back_populates="payments")
    company = relationship("Company", back_populates="payments")

    def __repr__(self):
        return f"<Payment {self.payment_ref}: ₹{self.amount}>"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=True)
    type = Column(Enum(NotificationType), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    user = relationship("User", back_populates="notifications")
    candidate = relationship("Candidate", back_populates="notifications")

    def __repr__(self):
        return f"<Notification {self.type}: {self.title}>"


class CandidateTimeline(Base):
    __tablename__ = "candidate_timeline"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    event_type = Column(String(50), nullable=False)
    event_date = Column(DateTime, default=func.now())
    title = Column(String(200), nullable=False)
    description = Column(Text)
    performed_by = Column(String(100))

    # Relationships
    candidate = relationship("Candidate", back_populates="timeline")

    def __repr__(self):
        return f"<Timeline {self.event_type} for candidate {self.candidate_id}>"


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(Integer)
    details = Column(Text)
    ip_address = Column(String(45))
    created_at = Column(DateTime, default=func.now())

    # Relationships
    user = relationship("User", back_populates="activity_logs")
    candidate = relationship("Candidate", back_populates="activity_logs")

    def __repr__(self):
        return f"<ActivityLog {self.action} by user {self.user_id}>"
