"""
Authentication System
RecruitPro CRM
"""

import bcrypt
import streamlit as st
from datetime import datetime
from typing import Optional
from database.connection import get_db
from database.models import User, UserRole, ActivityLog, Recruiter


# ─────────────────────────────────────────────────
# PASSWORD UTILITIES
# ─────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False


# ─────────────────────────────────────────────────
# SESSION MANAGEMENT
# ─────────────────────────────────────────────────

def init_session():
    """Initialize session state variables."""
    defaults = {
        "authenticated": False,
        "user_id": None,
        "username": None,
        "full_name": None,
        "role": None,
        "recruiter_id": None,
        "login_time": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def login(username: str, password: str) -> tuple[bool, str]:
    """Authenticate user and create session."""
    try:
        with get_db() as db:
            user = db.query(User).filter(
                User.username == username,
                User.is_active == True
            ).first()

            if not user:
                return False, "Invalid username or password"

            if not verify_password(password, user.password_hash):
                return False, "Invalid username or password"

            # Update last login
            user.last_login = datetime.now()

            # Log activity
            log = ActivityLog(
                user_id=user.id,
                action="LOGIN",
                entity_type="user",
                entity_id=user.id,
                details=f"User {username} logged in successfully"
            )
            db.add(log)

            # Set session
            st.session_state.authenticated = True
            st.session_state.user_id = user.id
            st.session_state.username = user.username
            st.session_state.full_name = user.full_name
            st.session_state.role = user.role.value
            st.session_state.login_time = datetime.now()

            # Set recruiter_id if applicable — explicit query avoids lazy-load issues
            recruiter = db.query(Recruiter).filter(Recruiter.user_id == user.id).first()
            if recruiter:
                st.session_state.recruiter_id = recruiter.id

            return True, "Login successful"

    except Exception as e:
        return False, f"Login error: {str(e)}"


def logout():
    """Clear session and logout."""
    if st.session_state.get("user_id"):
        try:
            with get_db() as db:
                log = ActivityLog(
                    user_id=st.session_state.user_id,
                    action="LOGOUT",
                    entity_type="user",
                    entity_id=st.session_state.user_id,
                    details=f"User {st.session_state.username} logged out"
                )
                db.add(log)
        except Exception:
            pass

    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_session()
    st.rerun()


def is_authenticated() -> bool:
    return st.session_state.get("authenticated", False)


def is_admin() -> bool:
    return st.session_state.get("role") == UserRole.ADMIN.value


def is_manager() -> bool:
    return st.session_state.get("role") in [UserRole.ADMIN.value, UserRole.MANAGER.value]


def require_auth():
    """Redirect to login if not authenticated."""
    if not is_authenticated():
        st.rerun()


def get_current_user() -> Optional[dict]:
    if not is_authenticated():
        return None
    return {
        "id": st.session_state.user_id,
        "username": st.session_state.username,
        "full_name": st.session_state.full_name,
        "role": st.session_state.role,
        "recruiter_id": st.session_state.get("recruiter_id"),
    }


# ─────────────────────────────────────────────────
# USER MANAGEMENT
# ─────────────────────────────────────────────────

def create_user(username: str, email: str, password: str, full_name: str,
                role: str, phone: str = "") -> tuple[bool, str]:
    try:
        with get_db() as db:
            existing = db.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()
            if existing:
                return False, "Username or email already exists"

            user = User(
                username=username,
                email=email,
                password_hash=hash_password(password),
                full_name=full_name,
                role=UserRole(role),
                phone=phone,
                is_active=True,
            )
            db.add(user)
            return True, "User created successfully"
    except Exception as e:
        return False, str(e)


def get_all_users() -> list:
    with get_db() as db:
        return db.query(User).filter(User.is_active == True).all()


def change_password(user_id: int, old_password: str, new_password: str) -> tuple[bool, str]:
    try:
        with get_db() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False, "User not found"
            if not verify_password(old_password, user.password_hash):
                return False, "Current password is incorrect"
            user.password_hash = hash_password(new_password)
            return True, "Password changed successfully"
    except Exception as e:
        return False, str(e)