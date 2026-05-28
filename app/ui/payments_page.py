"""
Payments Tracking Page
CRM
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import date
from sqlalchemy import func
from database.connection import get_db
from database.models import (
    Candidate, Company, Recruiter, User, PaymentStatus, CandidateStatus
)
from app.candidates.candidate_service import update_candidate
from app.utils.whatsapp import get_whatsapp_url, get_template_message

CHART_LAYOUT = dict(
    font_family="Plus Jakarta Sans",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=0, r=0, t=30, b=0),
)


def render_payments():
    st.markdown("""
    <div class="page-title">💰 Payment Tracking</div>
    <div class="page-subtitle">Track which companies have paid and which ones still need to pay.</div>
    """, unsafe_allow_html=True)

    with get_db() as db:
        total_pending = db.query(func.sum(Candidate.payment_amount)).filter(
            Candidate.payment_status == PaymentStatus.PENDING,
            Candidate.is_90_day_eligible == True,
        ).scalar() or 0

        total_overdue = db.query(func.sum(Candidate.payment_amount)).filter(
            Candidate.payment_status == PaymentStatus.OVERDUE,
        ).scalar() or 0

        total_received = db.query(func.sum(Candidate.payment_amount)).filter(
            Candidate.payment_status == PaymentStatus.RECEIVED,
        ).scalar() or 0

        pending_count = db.query(Candidate).filter(
            Candidate.payment_status.in_([PaymentStatus.PENDING, PaymentStatus.OVERDUE]),
            Candidate.is_90_day_eligible == True,
        ).count()

        received_count = db.query(Candidate).filter(
            Candidate.payment_status == PaymentStatus.RECEIVED,
        ).count()

    kc1, kc2, kc3, kc4, kc5 = st.columns(5)

    for col, label, val, icon, color in [
        (kc1, "Money Received", total_received, "✅", "#0E9F6E"),
        (kc2, "Money to Collect", total_pending, "⏳", "#FF8A4C"),
        (kc3, "Overdue (Not Paid)", total_overdue, "⚠️", "#F05252"),
    ]:
        col.markdown(f"""
        <div style="background:#1E293B;border:1px solid #334155;border-top:3px solid {color};
        border-radius:12px;padding:1.25rem;text-align:center;">
            <div style="font-size:1.5rem;margin-bottom:0.25rem;">{icon}</div>
            <div style="font-size:1.4rem;font-weight:800;color:{color};">₹{val:,.0f}</div>
            <div style="font-size:0.75rem;color:#64748B;font-weight:500;margin-top:3px;">{label}</div>
        </div>
        """, unsafe_allow_html=True)

    kc4.markdown(f"""
    <div style="background:#1E293B;border:1px solid #334155;border-top:3px solid #3B82F6;
    border-radius:12px;padding:1.25rem;text-align:center;">
        <div style="font-size:1.5rem;">🎯</div>
        <div style="font-size:1.4rem;font-weight:800;color:#3B82F6;">{pending_count}</div>
        <div style="font-size:0.75rem;color:#64748B;font-weight:500;margin-top:3px;">Companies to Follow Up</div>
    </div>
    """, unsafe_allow_html=True)

    kc5.markdown(f"""
    <div style="background:#1E293B;border:1px solid #334155;border-top:3px solid #0E9F6E;
    border-radius:12px;padding:1.25rem;text-align:center;">
        <div style="font-size:1.5rem;">💸</div>
        <div style="font-size:1.4rem;font-weight:800;color:#0E9F6E;">{received_count}</div>
        <div style="font-size:0.75rem;color:#64748B;font-weight:500;margin-top:3px;">Candidates Paid</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "⏳ Pending Payments",
        "✅ Received Payments",
        "📊 Analytics",
        "🧾 Generate Invoice"
    ])

    with tab1:
        _render_pending_payments()
    with tab2:
        _render_received_payments()
    with tab3:
        _render_payment_analytics()
    with tab4:
        from app.ui.invoice_page import render_invoice_generator
        render_invoice_generator()


def _render_pending_payments():
    st.markdown("### ⏳ Companies That Need to Pay")

    with get_db() as db:
        raw = (
            db.query(
                Candidate,
                Company.name.label("company_name"),
                User.full_name.label("recruiter_name"),
            )
            .outerjoin(Company, Candidate.company_id == Company.id)
            .outerjoin(Recruiter, Candidate.recruiter_id == Recruiter.id)
            .outerjoin(User, Recruiter.user_id == User.id)
            .filter(
                Candidate.payment_status.in_([PaymentStatus.PENDING, PaymentStatus.OVERDUE]),
                Candidate.is_90_day_eligible == True,
            )
            .order_by(Candidate.joining_date)
            .all()
        )
        results = []
        for row in raw:
            c = row.Candidate
            # Get company contact details
            company_phone = ""
            company_email = ""
            if c.company_id:
                comp = db.query(Company).filter(Company.id == c.company_id).first()
                if comp:
                    company_phone = comp.contact_phone or ""
                    company_email = comp.contact_email or ""

            results.append({
                "id": c.id,
                "candidate_id": c.candidate_id,
                "name": c.name,
                "phone": c.phone,
                "joining_date": c.joining_date,
                "payment_status": c.payment_status,
                "payment_amount": float(c.payment_amount or 0),
                "company_name": row.company_name or "—",
                "company_phone": company_phone,
                "company_email": company_email,
                "recruiter_name": row.recruiter_name or "—",
            })

    if not results:
        st.markdown("""
        <div style="text-align:center;padding:2rem;color:#64748B;">
            <div style="font-size:2.5rem;">🎉</div>
            <div style="font-weight:600;">No pending payments!</div>
        </div>
        """, unsafe_allow_html=True)
        return

    for row in results:
        days_since_90 = (date.today() - row["joining_date"]).days - 90 if row["joining_date"] else 0
        is_overdue = row["payment_status"] == PaymentStatus.OVERDUE
        joining_str = str(row["joining_date"]) if row["joining_date"] else "—"
        amount_str = f"{row['payment_amount']:,.0f}"
        cid = row["candidate_id"]
        name = row["name"]
        phone = row["phone"]
        company = row["company_name"]
        recruiter = row["recruiter_name"]

        payment_msg = get_template_message(
                "payment_confirmation",
                name=name,
                amount=amount_str,
            )

        col_info, col_action = st.columns([4, 1])

        with col_info:
            label_text = "⚠️ OVERDUE" if is_overdue else "⏳ Pending"
            st.markdown(f"**{label_text} — {name}** `{cid}`")
            st.caption(f"🏢 {company}  |  👤 {recruiter}  |  📅 Joined: {joining_str}  |  📱 {phone}")
            if is_overdue and days_since_90 > 0:
                st.warning(f"⚠️ {days_since_90} days overdue")
            st.markdown(f"**Placement Fee: ₹{amount_str}**")
            st.markdown("---")

        with col_action:
            st.markdown("<br>", unsafe_allow_html=True)

            # WhatsApp to COMPANY
            wa_company = get_whatsapp_url(row["company_phone"], payment_msg) if row["company_phone"] else "#"
            st.markdown(
                f'<a href="{wa_company}" target="_blank" style="display:flex;'
                f'justify-content:center;background:#25D366;color:white;'
                f'padding:0.4rem 0.6rem;border-radius:8px;font-size:0.8rem;'
                f'font-weight:600;text-decoration:none;margin-bottom:6px;">💬 WA Company</a>',
                unsafe_allow_html=True
            )

            # Email to COMPANY
            import urllib.parse
            email_subject = urllib.parse.quote(f"Payment Follow-up - {name}")
            email_body = urllib.parse.quote(
                f"Dear Team,\n\n"
                f"This is to inform you that {name} has successfully completed "
                f"90 days at your organization.\n\n"
                f"As per our agreement, the placement fee of Rs.{amount_str} "
                f"is now due.\n\n"
                f"Kindly arrange the payment at the earliest.\n\n"
                f"Thank you,\nCRM Team"
            )
            company_email = row["company_email"]
            gmail_url = f"https://mail.google.com/mail/?view=cm&to={company_email}&su={email_subject}&body={email_body}"
            st.markdown(
                f'<a href="{gmail_url}" target="_blank" style="display:flex;'
                f'justify-content:center;background:#EA4335;color:white;'
                f'padding:0.4rem 0.6rem;border-radius:8px;font-size:0.8rem;'
                f'font-weight:600;text-decoration:none;margin-bottom:6px;">📧 Email Company</a>',
                unsafe_allow_html=True
            )

            # Mark as received
            if st.button("✅ Mark Received", key=f"recv_{row['id']}", use_container_width=True):
                ok, msg = update_candidate(row["id"], {
                    "payment_status": PaymentStatus.RECEIVED.value,
                    "payment_received_date": date.today(),
                    "status": CandidateStatus.PAYMENT_RECEIVED.value,
                }, "Admin")
                if ok:
                    st.success("Payment marked as received!")
                    st.rerun()


def _render_received_payments():
    st.markdown("### ✅ Received Payments")

    with get_db() as db:
        raw = (
            db.query(
                Candidate,
                Company.name.label("company_name"),
                User.full_name.label("recruiter_name"),
            )
            .outerjoin(Company, Candidate.company_id == Company.id)
            .outerjoin(Recruiter, Candidate.recruiter_id == Recruiter.id)
            .outerjoin(User, Recruiter.user_id == User.id)
            .filter(Candidate.payment_status == PaymentStatus.RECEIVED)
            .order_by(Candidate.payment_received_date.desc())
            .limit(100)
            .all()
        )
        results = []
        total_recv = 0
        for row in raw:
            c = row.Candidate
            amt = float(c.payment_amount or 0)
            total_recv += amt
            results.append({
                "Candidate": c.name,
                "ID": c.candidate_id,
                "Company": row.company_name or "—",
                "Recruiter": row.recruiter_name or "—",
                "Amount": f"₹{amt:,.0f}",
                "Received Date": str(c.payment_received_date or "—"),
                "Invoice": c.invoice_number or "—",
            })

    if not results:
        st.info("No received payments yet.")
        return

    st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)
    st.markdown(
        f"<div style='text-align:right;font-weight:700;font-size:1rem;"
        f"color:#0E9F6E;margin-top:0.5rem;'>"
        f"Total Received: ₹{total_recv:,.0f}</div>",
        unsafe_allow_html=True
    )


def _render_payment_analytics():
    st.markdown("### 📊 Payment Analytics")

    with get_db() as db:
        company_data = (
            db.query(
                Company.name,
                func.sum(
                    func.IF(
                        Candidate.payment_status == PaymentStatus.PENDING,
                        Candidate.payment_amount, 0
                    )
                ).label("pending"),
                func.sum(
                    func.IF(
                        Candidate.payment_status == PaymentStatus.RECEIVED,
                        Candidate.payment_amount, 0
                    )
                ).label("received"),
            )
            .join(Candidate, Candidate.company_id == Company.id)
            .filter(Candidate.is_90_day_eligible == True)
            .group_by(Company.id, Company.name)
            .all()
        )
        comp_df = pd.DataFrame([{
            "company": r.name,
            "pending": float(r.pending or 0),
            "received": float(r.received or 0),
        } for r in company_data])

    if comp_df.empty:
        st.info("No analytics data available yet.")
        return

    ac1, ac2 = st.columns(2)

    with ac1:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=comp_df["company"], x=comp_df["pending"],
            name="Pending", orientation="h", marker_color="#FF8A4C"
        ))
        fig.add_trace(go.Bar(
            y=comp_df["company"], x=comp_df["received"],
            name="Received", orientation="h", marker_color="#0E9F6E"
        ))
        fig.update_layout(
            **CHART_LAYOUT, height=350, barmode="stack",
            title="Company-wise Payment Status",
            xaxis=dict(tickprefix="₹", showgrid=True, gridcolor="#334155"),
            yaxis=dict(showgrid=False),
        )
        st.plotly_chart(fig, use_container_width=True)

    with ac2:
        total_pending = comp_df["pending"].sum()
        total_received = comp_df["received"].sum()
        fig2 = go.Figure(data=[go.Pie(
            labels=["Pending", "Received"],
            values=[total_pending, total_received],
            hole=0.6,
            marker_colors=["#FF8A4C", "#0E9F6E"],
        )])
        fig2.update_layout(**CHART_LAYOUT, height=350, title="Overall Collection Rate")
        fig2.add_annotation(
            text=f"₹{total_received:,.0f}",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="#F1F5F9"),
        )
        st.plotly_chart(fig2, use_container_width=True)