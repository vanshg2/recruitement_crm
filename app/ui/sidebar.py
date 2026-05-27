"""
Sidebar Navigation
BLACKWOODS CRM
"""

import streamlit as st
from app.auth.auth import logout, is_admin, get_current_user
from app.dashboard.analytics import get_dashboard_kpis


def render_sidebar() -> str:
    user = get_current_user()
    kpis = get_dashboard_kpis()
    unread = kpis.get("unread_notifications", 0)
    alerts = kpis.get("alerts_90_day", 0)

    if "current_page" not in st.session_state:
        st.session_state.current_page = "Dashboard"

    with st.sidebar:
        st.markdown(f"### 🎯 BLACKWOODS CRM")
        st.markdown(f"👤 **{user['full_name']}** — {user['role'].title()}")
        st.markdown("---")

        pages = [
            ("🏠 Dashboard", "Dashboard"),
            ("👥 Candidates", "Candidates"),
            ("➕ Add Candidate", "Add Candidate"),
            ("💼 Recruiters", "Recruiters"),
            ("💰 Payments", "Payments"),
            ("🏢 Companies", "Companies"),
            (f"🔔 Notifications {'🔴' if unread > 0 else ''}", "Notifications"),
        ]

        if is_admin():
            pages.append(("⚙️ Settings", "Settings"))

        for label, page in pages:
            if st.button(label, key=f"nav_{page}", use_container_width=True):
                st.session_state.current_page = page
                st.rerun()

        st.markdown("---")
        st.markdown(f"🎯 **90-Day Alerts:** {alerts}")
        st.markdown(f"🔔 **Unread:** {unread}")
        st.markdown("---")

        if st.button("🚪 Sign Out", use_container_width=True):
            logout()

    return st.session_state.current_page