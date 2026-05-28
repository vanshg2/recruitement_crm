"""
Candidates Management Page
RecruitPro CRM
"""

import streamlit as st
import pandas as pd
from datetime import date
from database.connection import get_db
from database.models import Company, Recruiter, User, CandidateStatus, PaymentStatus, \
    Candidate, CandidateTimeline, ActivityLog, Notification
from app.candidates.candidate_service import (
    get_all_candidates, delete_candidate, export_candidates_excel
)
from app.utils.whatsapp import get_whatsapp_url


def render_candidates():
    # Show edit form if edit button was clicked
    if st.session_state.get("show_edit_form") and st.session_state.get("editing_candidate_id"):
        from app.ui.add_candidate_page import _render_candidate_form
        st.markdown("### ✏️ Edit Candidate")
        _render_candidate_form(is_edit=True)
        if st.button("← Back to Candidates List", key="back_to_list"):
            st.session_state.show_edit_form = False
            st.session_state.editing_candidate_id = None
            st.rerun()
        return

    st.markdown("""
    <div class="page-title">👥 Candidate Management</div>
    <div class="page-subtitle">View, search, and manage all candidates in your pipeline.</div>
    """, unsafe_allow_html=True)

    # Filters Row
    with st.expander("🔍 Search & Filters", expanded=True):
        fc1, fc2, fc3, fc4, fc5 = st.columns(5)
        with fc1:
            search = st.text_input("Search", placeholder="Name, phone, company...", label_visibility="collapsed", key="search_input")
        with fc2:
            status_options = ["All Statuses"] + [s.value for s in CandidateStatus]
            status_filter = st.selectbox("Status", status_options, label_visibility="collapsed")
        with fc3:
            payment_options = ["All Payments"] + [p.value for p in PaymentStatus]
            payment_filter = st.selectbox("Payment", payment_options, label_visibility="collapsed")
        with fc4:
            with get_db() as db:
                companies = db.query(Company).filter(Company.is_active == True).all()
                company_opts = {"All Companies": None}
                company_opts.update({c.name: c.id for c in companies})
            company_sel = st.selectbox("Company", list(company_opts.keys()), label_visibility="collapsed")
        with fc5:
            col_exp, col_refresh = st.columns(2)
            with col_exp:
                export_btn = st.button("📥 Export Excel", use_container_width=True)
            with col_refresh:
                if st.button("🔄 Refresh", use_container_width=True):
                    st.rerun()

    # Fetch Data
    st.write(f"DEBUG — role: {st.session_state.get('role')}, recruiter_id: {st.session_state.get('recruiter_id')}")
    candidates = get_all_candidates(
        search=search,
        status_filter="" if status_filter == "All Statuses" else status_filter,
        company_id=company_opts.get(company_sel),
        payment_status="" if payment_filter == "All Payments" else payment_filter,
    )

    # Export
    if export_btn:
        with st.spinner("Preparing Excel file..."):
            excel_data = export_candidates_excel(candidates)
        if excel_data:
            st.download_button(
                "⬇️ Click here to Download Excel",
                data=excel_data,
                file_name=f"candidates_{date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_excel_btn",
            )
        else:
            st.error("No data to export.")

    # Stats Row
    total = len(candidates)
    joined = sum(1 for c in candidates if c["status"] in [
        "Joined", "Completed 30 Days", "Completed 60 Days", "Completed 90 Days"
    ])
    eligible = sum(1 for c in candidates if c["is_90_day_eligible"] and c["payment_status"] == "Pending")
    pending_rev = sum(c["payment_amount"] for c in candidates if c["payment_status"] == "Pending" and c["is_90_day_eligible"])

    s1, s2, s3, s4 = st.columns(4)
    for col, label, val, color in [
        (s1, "Total Results", total, "#1C64F2"),
        (s2, "Currently Joined", joined, "#0E9F6E"),
        (s3, "Payment Eligible", eligible, "#FF8A4C"),
        (s4, "Pending Revenue", f"₹{pending_rev:,.0f}" if st.session_state.get("role") == "admin" else "—", "#7E3AF2"),
    ]:
        col.markdown(f"""
        <div style="background:white; border:1px solid #E5E7EB; border-radius:10px; padding:0.875rem 1.25rem; text-align:center;">
            <div style="font-size:1.4rem; font-weight:800; color:{color};">{val}</div>
            <div style="font-size:0.75rem; color:#6B7280; font-weight:500; margin-top:2px;">{label}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if not candidates:
        st.markdown("""
        <div style="text-align:center; padding:3rem; color:#9CA3AF;">
            <div style="font-size:3rem; margin-bottom:1rem;">🔍</div>
            <div style="font-size:1rem; font-weight:600;">No candidates found</div>
            <div style="font-size:0.875rem; margin-top:0.5rem;">Try adjusting your search filters</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # View toggle
    view_col, _ = st.columns([1, 4])
    with view_col:
        view_mode = st.radio("View", ["Table", "Cards"], horizontal=True, label_visibility="collapsed")

    if view_mode == "Table":
        _render_table_view(candidates)
    else:
        _render_card_view(candidates)

    # ── Danger Zone ───────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("⚠️ Danger Zone", expanded=False):
        st.markdown("""
        <div style="background:#450A0A; border:1px solid #991B1B; border-radius:10px; padding:1rem 1.25rem;">
            <div style="font-size:0.95rem; font-weight:700; color:#FCA5A5; margin-bottom:0.4rem;">
                🗑️ Clear All Data
            </div>
            <div style="font-size:0.8rem; color:#FCA5A5; opacity:0.85;">
                This will permanently delete <strong>all candidates</strong>, their timelines,
                activity logs, notifications,Recruiters data,Companies Data.
                <br><br>
                <strong>This action cannot be undone.</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Step 1 — show the button
        if not st.session_state.get("confirm_clear_step1"):
            if st.button("🗑️ Clear All Data", type="primary", use_container_width=True, key="clear_btn"):
                st.session_state.confirm_clear_step1 = True
                st.rerun()

        # Step 2 — first confirmation
        elif not st.session_state.get("confirm_clear_step2"):
            st.warning("⚠️ Are you sure? This will delete ALL candidates and sample data.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Yes, I'm sure", type="primary", use_container_width=True, key="clear_confirm1"):
                    st.session_state.confirm_clear_step2 = True
                    st.rerun()
            with c2:
                if st.button("Cancel", use_container_width=True, key="clear_cancel1"):
                    st.session_state.confirm_clear_step1 = False
                    st.rerun()

        # Step 3 — second (final) confirmation with text input
        else:
            st.error("🔴 Final confirmation required. Type **DELETE** to proceed.")
            confirm_text = st.text_input("Type DELETE to confirm", key="delete_confirm_text")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🗑️ Delete Everything", type="primary", use_container_width=True,
                             key="clear_final", disabled=(confirm_text != "DELETE")):
                    _run_clear_all_data()
            with c2:
                if st.button("Cancel", use_container_width=True, key="clear_cancel2"):
                    st.session_state.confirm_clear_step1 = False
                    st.session_state.confirm_clear_step2 = False
                    st.rerun()


def _run_clear_all_data():
    """Runs the same logic as delete_candidates.py — clears all candidates + sample data."""
    try:
        results = []
        with get_db() as db:
            # Delete candidate-linked records first
            notif_count = db.query(Notification).filter(Notification.candidate_id != None).delete(synchronize_session=False)
            db.query(CandidateTimeline).delete(synchronize_session=False)
            db.query(ActivityLog).filter(ActivityLog.candidate_id != None).delete(synchronize_session=False)

            cand_count = db.query(Candidate).count()
            db.query(Candidate).delete(synchronize_session=False)
            results.append(f"✅ Deleted {cand_count} candidates")

            # Delete sample recruiters
            sample_usernames = ['neha', 'amit', 'pooja']
            for username in sample_usernames:
                user = db.query(User).filter(User.username == username).first()
                if user:
                    rec = db.query(Recruiter).filter(Recruiter.user_id == user.id).first()
                    if rec:
                        db.delete(rec)
                    db.delete(user)
                    results.append(f"✅ Deleted recruiter: {username}")

            # Delete sample companies
            sample_companies = ['TechCorp Solutions', 'FinServ India', 'MediCare Hospitals']
            for name in sample_companies:
                comp = db.query(Company).filter(Company.name == name).first()
                if comp:
                    db.delete(comp)
                    results.append(f"✅ Deleted company: {name}")

            db.commit()

        # Reset confirmation state
        st.session_state.confirm_clear_step1 = False
        st.session_state.confirm_clear_step2 = False

        st.success("🎉 All sample data cleared successfully!")
        for line in results:
            st.write(line)
        st.rerun()

    except Exception as e:
        st.error(f"❌ Error during deletion: {e}")
        st.session_state.confirm_clear_step1 = False
        st.session_state.confirm_clear_step2 = False


def _render_table_view(candidates: list):
    PAGE_SIZE = 20
    total = len(candidates)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)

    if "cand_page" not in st.session_state:
        st.session_state.cand_page = 1

    page = st.session_state.cand_page
    start = (page - 1) * PAGE_SIZE
    page_candidates = candidates[start: start + PAGE_SIZE]

    # Build dataframe
    rows = []
    for c in page_candidates:
        rows.append({
            "ID": c["candidate_id"],
            "Name": (("🔴 ") if (c["is_90_day_eligible"] and c["payment_status"] == "Pending") else "") + c["name"],
            "Phone": c["phone"],
            "Company": c["company_name"],
            "Recruiter": c["recruiter_name"],
            "Status": c["status"],
            "Payment": c["payment_status"],
            "Salary (₹)": f"₹{c['ctc']:,.0f}" if c.get("ctc") and c["ctc"] > 0 else "—",
            "Commission (₹)": f"₹{c['payment_amount']:,.0f}" if st.session_state.get("role") == "admin" else "—",
            "Days": c["days_since_joining"] if c["days_since_joining"] is not None else "—",
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Action buttons
    st.markdown("**Quick Actions**")
    for i, c in enumerate(page_candidates):
        wa_link = get_whatsapp_url(c["phone"])
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        with col1:
            st.write(f"**{c['name']}** — {c['candidate_id']}")
        with col2:
            st.markdown(
                f'<a href="{wa_link}" target="_blank" style="background:#25D366;color:white;'
                f'padding:0.3rem 0.75rem;border-radius:999px;font-size:0.8rem;'
                f'font-weight:600;text-decoration:none;">💬 WA</a>',
                unsafe_allow_html=True
            )
        with col3:
            if st.button("✏️ Edit", key=f"edit_{i}_{c['id']}"):
                st.session_state.editing_candidate_id = c["id"]
                st.session_state.show_edit_form = True
                st.rerun()
        with col4:
            if st.button("🗑️ Del", key=f"del_{i}_{c['id']}"):
                st.session_state[f"confirm_delete_{i}_{c['id']}"] = True

        if st.session_state.get(f"confirm_delete_{i}_{c['id']}"):
            st.warning(f"Delete **{c['name']}**?")
            cc1, cc2 = st.columns(2)
            with cc1:
                if st.button("Yes", key=f"yes_{i}_{c['id']}", type="primary"):
                    ok, msg = delete_candidate(c["id"])
                    if ok:
                        st.success(msg)
                        st.rerun()
            with cc2:
                if st.button("No", key=f"no_{i}_{c['id']}"):
                    del st.session_state[f"confirm_delete_{i}_{c['id']}"]
                    st.rerun()

    # Pagination
    if total_pages > 1:
        st.markdown("<br>", unsafe_allow_html=True)
        p1, p2, p3 = st.columns([1, 2, 1])
        with p1:
            if st.button("← Previous", key="prev_page", disabled=page <= 1):
                st.session_state.cand_page -= 1
                st.rerun()
        with p2:
            st.markdown(
                f"<div style='text-align:center;color:#6B7280;padding-top:0.5rem;'>"
                f"Page {page} of {total_pages} ({total} total)</div>",
                unsafe_allow_html=True
            )
        with p3:
            if st.button("Next →", key="next_page", disabled=page >= total_pages):
                st.session_state.cand_page += 1
                st.rerun()


def _render_card_view(candidates: list):
    PAGE_SIZE = 30
    total = len(candidates)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)

    if "card_page" not in st.session_state:
        st.session_state.card_page = 1

    page = st.session_state.card_page
    start = (page - 1) * PAGE_SIZE
    page_candidates = candidates[start: start + PAGE_SIZE]

    for i in range(0, len(page_candidates), 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            if i + j >= len(page_candidates):
                break
            c = page_candidates[i + j]
            with col:
                alert = c["is_90_day_eligible"] and c["payment_status"] == "Pending"
                wa_link = get_whatsapp_url(c["phone"] if c["phone"] != "0000000000" else "")

                border_color = '#FCD34D' if alert else '#334155'
                top_color = '#F59E0B' if alert else '#3B82F6'
                name_prefix = '🔴 ' if alert else ''
                alert_html = '<div style="background:#78350F;border-radius:6px;padding:0.4rem 0.6rem;font-size:0.75rem;font-weight:600;color:#FDE68A;margin-bottom:0.5rem;">Payment Due - 90 days complete!</div>' if alert else ''

                name = c['name']
                cid = c['candidate_id']
                phone = c['phone'] if c['phone'] != '0000000000' else '—'
                company = c['company_name']
                recruiter = c['recruiter_name']
                status = c['status'][:14]
                pay_status = c['payment_status']
                amount = f"{c['payment_amount']:,.0f}"
                joining = str(c['joining_date']) if c.get('joining_date') else 'Not joined yet'
                days = c.get('days_since_joining')
                days_display = f"{days} days" if days is not None else "—"
                salary = f"₹{c['ctc']:,.0f}" if c.get('ctc') and c['ctc'] > 0 else "—"

                html = (
                    f'<div style="background:#1E293B;border:1px solid {border_color};'
                    f'border-top:3px solid {top_color};border-radius:12px;padding:1.25rem;'
                    f'margin-bottom:1rem;box-shadow:0 1px 3px rgba(0,0,0,.2);">'
                    f'<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.875rem;">'
                    f'<div><div style="font-weight:700;font-size:0.95rem;color:#F1F5F9;">{name_prefix}{name}</div>'
                    f'<div style="font-size:0.75rem;color:#64748B;">{cid}</div></div>'
                    f'<span style="background:#0F172A;color:#94A3B8;font-size:0.72rem;font-weight:600;padding:0.2rem 0.6rem;border-radius:999px;">{status}</span>'
                    f'</div>'
                    f'<div style="font-size:0.8rem;color:#94A3B8;margin-bottom:0.5rem;">'
                    f'📱 {phone}<br>🏢 {company}<br>👤 {recruiter}<br>'
                    f'📅 Joined: {joining}<br>'
                    f'💰 Salary: {salary}<br>'\
                    f'⏳ Days: {days_display}</div>'
                    f'{alert_html}'
                    f'<div style="display:flex;justify-content:space-between;align-items:center;margin-top:0.75rem;padding-top:0.75rem;border-top:1px solid #334155;">'
                    f'<div><span style="background:#78350F;color:#FCD34D;font-size:0.72rem;font-weight:600;padding:0.2rem 0.6rem;border-radius:999px;">{pay_status}</span>'
                    f'<span style="font-size:0.8rem;font-weight:700;color:#10B981;margin-left:8px;">{"Commission: ₹" + amount if st.session_state.get("role") == "admin" else "—"}</span></div>'
                    f'<a href="{wa_link}" target="_blank" style="background:#25D366;color:white;padding:0.4rem 0.875rem;border-radius:999px;font-size:0.8rem;font-weight:600;text-decoration:none;">💬 WhatsApp</a>'
                    f'</div></div>'
                )
                st.markdown(html, unsafe_allow_html=True)

    # Pagination
    if total_pages > 1:
        st.markdown("<br>", unsafe_allow_html=True)
        p1, p2, p3 = st.columns([1, 2, 1])
        with p1:
            if st.button("← Previous", key="card_prev", disabled=page <= 1):
                st.session_state.card_page -= 1
                st.rerun()
        with p2:
            st.markdown(
                f"<div style='text-align:center;color:#64748B;padding-top:0.5rem;'>"
                f"Page {page} of {total_pages} ({total} candidates)</div>",
                unsafe_allow_html=True
            )
        with p3:
            if st.button("Next →", key="card_next", disabled=page >= total_pages):
                st.session_state.card_page += 1
                st.rerun()