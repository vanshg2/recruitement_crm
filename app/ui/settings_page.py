"""
Settings Page
BLACKWOODS CRM
"""

import streamlit as st
from database.connection import get_db
from database.models import User
from app.auth.auth import get_current_user, change_password, verify_password


def render_settings():
    user = get_current_user()

    st.markdown("""
    <div class="page-title">Settings</div>
    <div class="page-subtitle">Change your username and password.</div>
    """, unsafe_allow_html=True)

    st.markdown("### Change Username")
    with st.form("change_username_form", clear_on_submit=True):
        current_password = st.text_input("Current Password", type="password")
        new_username = st.text_input("New Username")

        if st.form_submit_button("Update Username", type="primary"):
            if not current_password or not new_username:
                st.error("Please fill all fields.")
            else:
                with get_db() as db:
                    u = db.query(User).filter(User.id == user["id"]).first()
                    if not u:
                        st.error("User not found.")
                    elif not verify_password(current_password, u.password_hash):
                        st.error("Current password is incorrect.")
                    else:
                        existing = db.query(User).filter(
                            User.username == new_username.strip(),
                            User.id != user["id"]
                        ).first()
                        if existing:
                            st.error("Username already taken.")
                        else:
                            u.username = new_username.strip()
                            st.success("Username updated successfully!")

    st.markdown("---")

    st.markdown("### Change Password")
    with st.form("change_password_form", clear_on_submit=True):
        current_pw = st.text_input("Current Password", type="password")
        new_pw = st.text_input("New Password", type="password")
        confirm_pw = st.text_input("Confirm New Password", type="password")

        if st.form_submit_button("Update Password", type="primary"):
            if not current_pw or not new_pw or not confirm_pw:
                st.error("Please fill all fields.")
            elif new_pw != confirm_pw:
                st.error("New passwords do not match.")
            elif len(new_pw) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                ok, msg = change_password(user["id"], current_pw, new_pw)
                if ok:
                    st.success("Password updated successfully!")
                else:
                    st.error(msg)
