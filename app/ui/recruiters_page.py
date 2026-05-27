"""
Recruiters Management Page
RecruitPro CRM
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import date
from sqlalchemy import func
from database.connection import get_db
from database.models import (
    Recruiter, User, Candidate, UserRole,
    CandidateStatus, PaymentStatus
)
from app.auth.auth import create_user, is_admin

CHART_LAYOUT = dict(
    font_family="Plus Jakarta Sans",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=0, r=0, t=30, b=0),
)


def _get_recruiter_stats() -> list:
    with get_db() as db:
        recruiters = (
            db.query(Recruiter, User)
            .join(User, Recruiter.user_id == User.id)
            .filter(Recruiter.is_active == True, User.is_active == True)
            .all()
        )

        stats = []
        for rec, usr in recruiters:
            base = db.query(Candidate).filter(Candidate.recruiter_id == rec.id)
            total = base.count()
            joined = base.filter(Candidate.status.in_([
                CandidateStatus.JOINED,
                CandidateStatus.COMPLETED_30,
                CandidateStatus.COMPLETED_60,
                CandidateStatus.COMPLETED_90,
                CandidateStatus.PAYMENT_PENDING,
                CandidateStatus.PAYMENT_RECEIVED,
            ])).count()
            drops = base.filter(Candidate.status == CandidateStatus.DROP).count()
            active = base.filter(Candidate.status.in_([
                CandidateStatus.INTERVIEW_SCHEDULED,
                CandidateStatus.SELECTED,
            ])).count()
            revenue = db.query(func.sum(Candidate.payment_amount)).filter(
                Candidate.recruiter_id == rec.id,
                Candidate.payment_status == PaymentStatus.RECEIVED,
            ).scalar() or 0
            pending = db.query(func.sum(Candidate.payment_amount)).filter(
                Candidate.recruiter_id == rec.id,
                Candidate.payment_status == PaymentStatus.PENDING,
                Candidate.is_90_day_eligible == True,
            ).scalar() or 0

            conversion = round((joined / total * 100), 1) if total > 0 else 0

            stats.append({
                "id": rec.id,
                "user_id": usr.id,
                "name": usr.full_name,
                "username": usr.username,
                "email": usr.email,
                "phone": usr.phone or "—",
                "department": rec.department or "—",
                "specialization": rec.specialization or "—",
                "joining_date": rec.joining_date,
                "target_monthly": rec.target_monthly,
                "total": total,
                "active": active,
                "joined": joined,
                "drops": drops,
                "revenue": float(revenue),
                "pending": float(pending),
                "conversion": conversion,
            })

        stats.sort(key=lambda x: x["revenue"], reverse=True)
        return stats


def render_recruiters():
    st.markdown("""
    <div class="page-title">💼 Recruiter Management</div>
    <div class="page-subtitle">Track recruiter performance, manage team, and monitor targets.</div>
    """, unsafe_allow_html=True)

    if is_admin():
        tab1, tab2, tab3, tab4 = st.tabs(["🏆 Leaderboard", "📊 Analytics", "➕ Add Recruiter", "🗑️ Remove Recruiter"])
    else:
        tab1, tab2 = st.tabs(["🏆 Leaderboard", "📊 Analytics"])

    with tab1:
        _render_leaderboard()
    with tab2:
        _render_analytics()

    if is_admin():
        with tab3:
            _render_add_recruiter()
        with tab4:
            _render_remove_recruiter()


def _render_leaderboard():
    stats = _get_recruiter_stats()

    if not stats:
        st.markdown("""
        <div style="text-align:center; padding:3rem; color:#9CA3AF;">
            <div style="font-size:3rem;">👥</div>
            <div style="font-weight:600; margin-top:0.5rem;">No recruiters found</div>
            <div style="font-size:0.875rem;">Add recruiters from the Add Recruiter tab.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Team KPIs
    total_candidates = sum(r["total"] for r in stats)
    total_revenue = sum(r["revenue"] for r in stats)
    avg_conversion = round(sum(r["conversion"] for r in stats) / len(stats), 1) if stats else 0

    kc1, kc2, kc3, kc4 = st.columns(4)
    kc1.metric("Team Size", len(stats))
    kc2.metric("Total Candidates", total_candidates)
    kc3.metric("Total Revenue", f"₹{total_revenue:,.0f}")
    kc4.metric("Avg Conversion", f"{avg_conversion}%")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")

    medals = ["🥇", "🥈", "🥉"]

    for rank, r in enumerate(stats):
        medal = medals[rank] if rank < 3 else f"#{rank+1}"

        c1, c2, c3, c4, c5, c6, c7 = st.columns([0.5, 2, 1, 1, 1, 1.5, 1.5])

        with c1:
            st.markdown(f"<div style='font-size:1.5rem;text-align:center;padding-top:0.5rem;'>{medal}</div>",
                        unsafe_allow_html=True)
        with c2:
            st.markdown(f"**{r['name']}**")
            st.caption(f"@{r['username']} · {r['department']}")
        with c3:
            st.metric("Total", r["total"])
        with c4:
            st.metric("Joined", r["joined"])
        with c5:
            st.metric("Drops", r["drops"])
        with c6:
            st.metric("Revenue", f"₹{r['revenue']:,.0f}")
        with c7:
            st.metric("Conversion", f"{r['conversion']}%")

        with st.expander(f"📋 Details — {r['name']}"):
            st.markdown(f"""
            <div style="display:grid; grid-template-columns:repeat(3,1fr); gap:0.75rem; padding:0.5rem 0;">
                <div style="background:#0F172A; border:1px solid #334155; border-radius:10px; padding:0.875rem 1.1rem;">
                    <div style="font-size:0.72rem; color:#64748B; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px;">Email</div>
                    <div style="font-size:0.85rem; font-weight:600; color:#93C5FD; word-break:break-all;">{r['email']}</div>
                </div>
                <div style="background:#0F172A; border:1px solid #334155; border-radius:10px; padding:0.875rem 1.1rem;">
                    <div style="font-size:0.72rem; color:#64748B; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px;">Phone</div>
                    <div style="font-size:0.85rem; font-weight:600; color:#F1F5F9;">{r['phone']}</div>
                </div>
                <div style="background:#0F172A; border:1px solid #334155; border-radius:10px; padding:0.875rem 1.1rem;">
                    <div style="font-size:0.72rem; color:#64748B; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px;">Monthly Target</div>
                    <div style="font-size:0.85rem; font-weight:600; color:#F1F5F9;">{r['target_monthly']} candidates</div>
                </div>
                <div style="background:#0F172A; border:1px solid #334155; border-radius:10px; padding:0.875rem 1.1rem;">
                    <div style="font-size:0.72rem; color:#64748B; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px;">Active Pipeline</div>
                    <div style="font-size:0.85rem; font-weight:600; color:#F1F5F9;">{r['active']}</div>
                </div>
                <div style="background:#0F172A; border:1px solid #334155; border-radius:10px; padding:0.875rem 1.1rem;">
                    <div style="font-size:0.72rem; color:#64748B; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px;">Pending Collection</div>
                    <div style="font-size:0.85rem; font-weight:600; color:#F59E0B;">₹{r['pending']:,.0f}</div>
                </div>
                <div style="background:#0F172A; border:1px solid #334155; border-radius:10px; padding:0.875rem 1.1rem;">
                    <div style="font-size:0.72rem; color:#64748B; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px;">Joining Date</div>
                    <div style="font-size:0.85rem; font-weight:600; color:#F1F5F9;">{str(r['joining_date']) if r['joining_date'] else '—'}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")


def _render_analytics():
    stats = _get_recruiter_stats()
    if not stats:
        st.info("No recruiter data available.")
        return

    df = pd.DataFrame(stats)

    ac1, ac2 = st.columns(2)

    with ac1:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df["name"], y=df["joined"],
            name="Joined", marker_color="#1C64F2", marker_line_width=0,
        ))
        fig.add_trace(go.Bar(
            x=df["name"], y=df["drops"],
            name="Drops", marker_color="#F05252", marker_line_width=0,
        ))
        fig.update_layout(
            **CHART_LAYOUT, height=320, barmode="group",
            title="Joins vs Drops by Recruiter",
            xaxis=dict(showgrid=False, tickangle=-20),
            yaxis=dict(showgrid=True, gridcolor="#F3F4F6"),
        )
        st.plotly_chart(fig, use_container_width=True)

    with ac2:
        fig2 = px.bar(
            df, x="name", y="revenue",
            color="revenue",
            color_continuous_scale=["#EBF2FF", "#1C64F2"],
            labels={"name": "Recruiter", "revenue": "Revenue (₹)"},
            title="Revenue Generated by Recruiter",
        )
        fig2.update_layout(
            **CHART_LAYOUT, height=320,
            xaxis=dict(showgrid=False, tickangle=-20),
            yaxis=dict(showgrid=True, gridcolor="#F3F4F6", tickprefix="₹"),
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig2, use_container_width=True)

    fig3 = px.bar(
        df.sort_values("conversion", ascending=True),
        x="conversion", y="name", orientation="h",
        color="conversion",
        color_continuous_scale=["#FDE8E8", "#0E9F6E"],
        labels={"conversion": "Conversion Rate (%)", "name": ""},
        title="Recruiter Conversion Rate (%)",
        text="conversion",
    )
    fig3.update_traces(texttemplate="%{text}%", textposition="outside")
    fig3.update_layout(
        **CHART_LAYOUT, height=300,
        coloraxis_showscale=False,
        xaxis=dict(showgrid=True, gridcolor="#F3F4F6"),
    )
    st.plotly_chart(fig3, use_container_width=True)


def _render_add_recruiter():
    st.markdown("### ➕ Add New Recruiter")

    with st.form("add_recruiter_form", clear_on_submit=True):
        st.markdown("**Account Information**")
        r1, r2 = st.columns(2)
        with r1:
            full_name = st.text_input("Full Name *")
            username = st.text_input("Username *")
        with r2:
            email = st.text_input("Email *")
            phone = st.text_input("Phone Number")

        password = st.text_input("Password *", type="password")

        st.markdown("---")
        st.markdown("**Professional Details**")
        p1, p2, p3 = st.columns(3)
        with p1:
            department = st.text_input("Department", placeholder="e.g. IT Recruitment")
        with p2:
            specialization = st.text_input("Specialization", placeholder="e.g. Tech, Healthcare")
        with p3:
            target_monthly = st.number_input("Monthly Target", min_value=0, value=10)

        joining_date = st.date_input("Joining Date", value=date.today(), min_value=date(2000, 1, 1))

        submitted = st.form_submit_button("➕ Create Recruiter", type="primary", use_container_width=True)

        if submitted:
            if not full_name or not username or not email or not password:
                st.error("Please fill all required fields (*)")
            else:
                ok, msg = create_user(
                    username=username.strip(),
                    email=email.strip(),
                    password=password,
                    full_name=full_name.strip(),
                    role=UserRole.RECRUITER.value,
                    phone=phone.strip(),
                )
                if ok:
                    with get_db() as db:
                        user = db.query(User).filter(User.username == username.strip()).first()
                        if user:
                            rec = Recruiter(
                                user_id=user.id,
                                employee_id=f"EMP{str(user.id).zfill(4)}",
                                department=department.strip(),
                                specialization=specialization.strip(),
                                target_monthly=target_monthly,
                                joining_date=joining_date,
                            )
                            db.add(rec)
                    st.success(f"✅ Recruiter {full_name} created successfully!")
                    st.balloons()
                else:
                    st.error(f"❌ {msg}")


def _render_remove_recruiter():
    st.markdown("### 🗑️ Remove Recruiter")

    with get_db() as db:
        recruiters = (
            db.query(Recruiter, User)
            .join(User, Recruiter.user_id == User.id)
            .filter(Recruiter.is_active == True, User.is_active == True)
            .all()
        )
        recruiter_list = [
            {
                "recruiter_id": rec.id,
                "user_id": usr.id,
                "name": usr.full_name,
                "username": usr.username,
                "email": usr.email,
                "total_candidates": db.query(Candidate).filter(Candidate.recruiter_id == rec.id).count(),
            }
            for rec, usr in recruiters
        ]

    if not recruiter_list:
        st.info("No recruiters found.")
        return

    # Recruiter selector
    options = {f"{r['name']} (@{r['username']})": r for r in recruiter_list}
    selected_label = st.selectbox("Select Recruiter to Remove", list(options.keys()))
    selected = options[selected_label]

    # Info card
    st.markdown(f"""
    <div style="background:#1E293B; border:1px solid #334155; border-radius:10px;
                padding:1rem 1.25rem; margin:1rem 0;">
        <div style="font-size:0.95rem; font-weight:700; color:#F1F5F9; margin-bottom:0.5rem;">
            {selected['name']}
        </div>
        <div style="font-size:0.82rem; color:#94A3B8;">
            👤 @{selected['username']} &nbsp;|&nbsp;
            📧 {selected['email']} &nbsp;|&nbsp;
            👥 {selected['total_candidates']} candidate(s) assigned
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Warning if they have candidates
    if selected["total_candidates"] > 0:
        st.warning(
            f"⚠️ **{selected['name']}** has **{selected['total_candidates']} candidate(s)** assigned. "
            f"Their candidates will remain in the system but will show no recruiter."
        )

    st.markdown("---")

    # Confirmation flow
    if not st.session_state.get("confirm_remove_recruiter"):
        if st.button("🗑️ Remove This Recruiter", type="primary", use_container_width=True, key="remove_rec_btn"):
            st.session_state.confirm_remove_recruiter = selected["user_id"]
            st.rerun()
    else:
        st.error(f"Are you sure you want to remove **{selected['name']}**? This will deactivate their login.")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Yes, Remove", type="primary", use_container_width=True, key="confirm_remove_yes"):
                _do_remove_recruiter(selected["recruiter_id"], selected["user_id"], selected["name"])
        with c2:
            if st.button("Cancel", use_container_width=True, key="confirm_remove_no"):
                st.session_state.confirm_remove_recruiter = None
                st.rerun()


def _do_remove_recruiter(recruiter_id: int, user_id: int, name: str):
    try:
        with get_db() as db:
            # Deactivate recruiter profile
            rec = db.query(Recruiter).filter(Recruiter.id == recruiter_id).first()
            if rec:
                rec.is_active = False

            # Deactivate user login
            usr = db.query(User).filter(User.id == user_id).first()
            if usr:
                usr.is_active = False

            db.commit()

        st.session_state.confirm_remove_recruiter = None
        st.success(f"✅ Recruiter **{name}** has been removed. Their login is now deactivated.")
        st.rerun()

    except Exception as e:
        st.error(f"❌ Error removing recruiter: {e}")