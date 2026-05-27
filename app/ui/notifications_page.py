"""
Notifications Page
BLACKWOODS CRM
"""

import streamlit as st
from app.dashboard.analytics import (
    get_unread_notifications, mark_notification_read, mark_all_notifications_read
)
from app.auth.auth import get_current_user
from database.connection import get_db
from database.models import Notification

NOTIF_ICONS = {
    "30_days": "📅",
    "60_days": "⏱",
    "90_days": "🎯",
    "payment_due": "💰",
    "payment_overdue": "⚠️",
    "general": "🔔",
}

NOTIF_COLORS = {
    "30_days": "#3B82F6",
    "60_days": "#8B5CF6",
    "90_days": "#F59E0B",
    "payment_due": "#10B981",
    "payment_overdue": "#EF4444",
    "general": "#64748B",
}

NOTIF_BG = {
    "30_days": "#1E3A5F",
    "60_days": "#3B0764",
    "90_days": "#78350F",
    "payment_due": "#064E3B",
    "payment_overdue": "#7F1D1D",
    "general": "#1E293B",
}


def render_notifications():
    user = get_current_user()

    st.markdown("""
    <div class="page-title">🔔 Notifications</div>
    <div class="page-subtitle">Stay on top of 90-day milestones, payment reminders and alerts.</div>
    """, unsafe_allow_html=True)

    # Auto refresh every 60 seconds
    st.markdown("""
    <script>
        setTimeout(function() { window.location.reload(); }, 60000);
    </script>
    """, unsafe_allow_html=True)

    notifications = get_unread_notifications(user["id"], limit=50)
    unread_count = sum(1 for n in notifications if not n["is_read"])
    read_count = sum(1 for n in notifications if n["is_read"])

    # Controls row
    c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 2])
    with c1:
        if unread_count > 0 and st.button(
            f"✅ Mark all as read ({unread_count})", use_container_width=True
        ):
            mark_all_notifications_read(user["id"])
            st.rerun()
    with c2:
        if read_count > 0 and st.button(
            f"🗑️ Delete read ({read_count})", use_container_width=True
        ):
            with get_db() as db:
                db.query(Notification).filter(
                    Notification.user_id == user["id"],
                    Notification.is_read == True
                ).delete(synchronize_session=False)
            st.success("Read notifications deleted!")
            st.rerun()
    with c3:
        filter_unread = st.checkbox("Unread only", value=False)
    with c4:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    with c5:
        if st.button("🎯 Check 90-Day Alerts", use_container_width=True, type="primary"):
            from app.utils.scheduler import run_day_tracking_now
            with st.spinner("Checking candidates..."):
                run_day_tracking_now()
            st.success("Done! New alerts generated.")
            st.rerun()

    if not notifications:
        st.markdown("""
        <div style="text-align:center; padding:4rem 2rem; color:#64748B;">
            <div style="font-size:3.5rem; margin-bottom:1rem;">🎉</div>
            <div style="font-size:1rem; font-weight:600; color:#CBD5E1;">You are all caught up!</div>
            <div style="font-size:0.875rem; margin-top:0.5rem;">No notifications at the moment.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    display = [n for n in notifications if (not filter_unread or not n["is_read"])]

    if not display:
        st.info("No unread notifications.")
        return

    st.markdown(f"**{len(display)} notification(s)**")
    st.markdown("<br>", unsafe_allow_html=True)

    for n in display:
        icon = NOTIF_ICONS.get(n["type"], "🔔")
        color = NOTIF_COLORS.get(n["type"], "#64748B")
        bg = NOTIF_BG.get(n["type"], "#1E293B")
        time_str = n["created_at"].strftime("%d %b %Y, %I:%M %p") if n["created_at"] else ""
        is_read = n["is_read"]
        unread_badge = "🔵 " if not is_read else ""

        col_content, col_actions = st.columns([5, 1])

        with col_content:
            st.markdown(f"""
            <div style="
                background:{bg};
                border:1px solid {'#475569' if not is_read else '#334155'};
                border-left:4px solid {color};
                border-radius:10px;
                padding:1rem 1.25rem;
                margin-bottom:0.5rem;
                opacity:{'1' if not is_read else '0.6'};
            ">
                <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.4rem;">
                    <span style="font-size:1.2rem;">{icon}</span>
                    <span style="font-weight:700;font-size:0.9rem;color:#F1F5F9;">{unread_badge}{n['title']}</span>
                </div>
                <div style="font-size:0.82rem;color:#CBD5E1;margin-bottom:0.4rem;">{n['message']}</div>
                <div style="font-size:0.72rem;color:#64748B;">🕐 {time_str}</div>
            </div>
            """, unsafe_allow_html=True)

        with col_actions:
            st.markdown("<br>", unsafe_allow_html=True)
            if not is_read:
                if st.button("✓", key=f"read_{n['id']}", help="Mark as read",
                             use_container_width=True):
                    mark_notification_read(n["id"])
                    st.rerun()
            if st.button("🗑", key=f"del_{n['id']}", help="Delete",
                         use_container_width=True):
                with get_db() as db:
                    notif = db.query(Notification).filter(
                        Notification.id == n["id"]
                    ).first()
                    if notif:
                        db.delete(notif)
                st.rerun()