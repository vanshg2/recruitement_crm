"""
Companies Management Page
Recruitment CRM
"""

import streamlit as st
import pandas as pd
from sqlalchemy import func
from database.connection import get_db
from database.models import Company, Candidate, PaymentStatus, CandidateStatus
from app.auth.auth import is_admin


def _get_companies_with_stats() -> list[dict]:
    with get_db() as db:
        companies = db.query(Company).filter(
            Company.is_active == True
        ).order_by(Company.name).all()

        result = []

        for c in companies:
            total = db.query(Candidate).filter(
                Candidate.company_id == c.id
            ).count()

            joined = db.query(Candidate).filter(
                Candidate.company_id == c.id,
                Candidate.status.in_([
                    CandidateStatus.JOINED,
                    CandidateStatus.COMPLETED_30,
                    CandidateStatus.COMPLETED_60,
                    CandidateStatus.COMPLETED_90,
                    CandidateStatus.PAYMENT_PENDING,
                    CandidateStatus.PAYMENT_RECEIVED,
                ])
            ).count()

            pending_rev = db.query(
                func.sum(Candidate.payment_amount)
            ).filter(
                Candidate.company_id == c.id,
                Candidate.payment_status == PaymentStatus.PENDING,
                Candidate.is_90_day_eligible == True,
            ).scalar() or 0

            recv_rev = db.query(
                func.sum(Candidate.payment_amount)
            ).filter(
                Candidate.company_id == c.id,
                Candidate.payment_status == PaymentStatus.RECEIVED,
            ).scalar() or 0

            result.append({
                "id": c.id,
                "name": c.name,
                "industry": c.industry or "—",
                "contact_person": c.contact_person or "—",
                "contact_email": c.contact_email or "—",
                "contact_phone": c.contact_phone or "—",
                "website": c.website or "",
                "total_candidates": total,
                "joined": joined,
                "pending_revenue": float(pending_rev),
                "received_revenue": float(recv_rev),
            })

        return result


def render_companies():
    st.markdown("""
    <div class="page-title">🏢 Company Management</div>
    <div class="page-subtitle">
        Manage client companies, track placements, and monitor revenue.
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🏢 All Companies", "➕ Add Company"])

    with tab1:
        _render_companies_list()

    with tab2:
        _render_add_company()


def _render_companies_list():
    companies = _get_companies_with_stats()

    if not companies:
        st.markdown("""
        <div style="text-align:center; padding:3rem; color:#9CA3AF;">
            <div style="font-size:3rem;">🏢</div>
            <div style="font-weight:600; margin-top:0.5rem;">
                No companies yet
            </div>
            <div style="font-size:0.875rem;">
                Add your client companies from the "Add Company" tab.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Summary KPIs
    total_companies = len(companies)
    total_pending = sum(c["pending_revenue"] for c in companies)
    total_received = sum(c["received_revenue"] for c in companies)
    total_candidates = sum(c["total_candidates"] for c in companies)

    kc1, kc2, kc3, kc4 = st.columns(4)

    for col, label, val, color, prefix in [
        (kc1, "Client Companies", total_companies, "#1C64F2", ""),
        (kc2, "Total Placements", total_candidates, "#7E3AF2", ""),
        (kc3, "Pending Revenue", total_pending, "#FF8A4C", "₹"),
        (kc4, "Collected Revenue", total_received, "#0E9F6E", "₹"),
    ]:
        col.metric(label, f"{prefix}{val:,.0f}")

    st.markdown("<br>", unsafe_allow_html=True)

    # Search
    search = st.text_input(
        "🔍 Search companies",
        placeholder="Company name, industry, contact..."
    )

    filtered = [
        c for c in companies
        if not search or search.lower() in (
            c["name"] +
            c["industry"] +
            c["contact_person"] +
            c["contact_email"]
        ).lower()
    ]

    # Company cards
    for c in filtered:

        with st.expander(
            f"🏢 {c['name']}  |  {c['industry']}  |  "
            f"{c['total_candidates']} placements"
            f"{' ⚠️' if c['pending_revenue'] > 0 else ''}"
        ):

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"**Contact Person:** {c['contact_person']}")
                st.markdown(f"**Email:** {c['contact_email']}")
                st.markdown(f"**Phone:** {c['contact_phone']}")
                if c["website"]:
                    st.markdown(f"**Website:** {c['website']}")

            with col2:
                st.metric("Total Candidates", c["total_candidates"])
                st.metric("Currently Joined", c["joined"])

            with col3:
                st.metric(
                    "Pending Revenue",
                    f"₹{c['pending_revenue']:,.0f}"
                )

                st.metric(
                    "Collected Revenue",
                    f"₹{c['received_revenue']:,.0f}"
                )

            # =========================================
            # EDIT COMPANY DETAILS
            # =========================================

            st.markdown("---")
            st.markdown("### ✏️ Edit Company Details")

            with st.form(key=f"edit_company_{c['id']}"):

                ec1, ec2 = st.columns(2)

                with ec1:
                    new_contact = st.text_input(
                        "Contact Person",
                        value=c["contact_person"]
                        if c["contact_person"] != "—"
                        else ""
                    )

                    new_email = st.text_input(
                        "Contact Email",
                        value=c["contact_email"]
                        if c["contact_email"] != "—"
                        else ""
                    )

                with ec2:
                    new_phone = st.text_input(
                        "Contact Phone",
                        value=c["contact_phone"]
                        if c["contact_phone"] != "—"
                        else ""
                    )

                    new_industry = st.text_input(
                        "Industry",
                        value=c["industry"]
                        if c["industry"] != "—"
                        else ""
                    )

                submitted = st.form_submit_button(
                    "💾 Save",
                    type="primary"
                )

                if submitted:

                    with get_db() as db:

                        comp = db.query(Company).filter(
                            Company.id == c["id"]
                        ).first()

                        if comp:
                            comp.contact_person = new_contact
                            comp.contact_email = new_email
                            comp.contact_phone = new_phone
                            comp.industry = new_industry

                            db.commit()

                    st.success("✅ Company updated successfully!")
                    st.rerun()

            # =========================================
            # DELETE COMPANY
            # =========================================

            if is_admin():

                ec1, ec2 = st.columns([1, 5])

                with ec1:

                    if st.button(
                        "🗑 Delete",
                        key=f"del_company_{c['id']}",
                        type="secondary"
                    ):
                        st.session_state[
                            f"confirm_del_company_{c['id']}"
                        ] = True

                if st.session_state.get(
                    f"confirm_del_company_{c['id']}"
                ):

                    st.warning(
                        f"Delete **{c['name']}**? "
                        f"This will not delete associated candidates."
                    )

                    cc1, cc2 = st.columns(2)

                    with cc1:

                        if st.button(
                            "Yes, delete",
                            key=f"yes_del_company_{c['id']}",
                            type="primary"
                        ):

                            with get_db() as db:

                                comp = db.query(Company).filter(
                                    Company.id == c["id"]
                                ).first()

                                if comp:
                                    comp.is_active = False
                                    db.commit()

                            st.success(
                                f"Company {c['name']} removed."
                            )

                            del st.session_state[
                                f"confirm_del_company_{c['id']}"
                            ]

                            st.rerun()

                    with cc2:

                        if st.button(
                            "Cancel",
                            key=f"no_del_company_{c['id']}"
                        ):

                            del st.session_state[
                                f"confirm_del_company_{c['id']}"
                            ]

                            st.rerun()


def _render_add_company():

    st.markdown("### ➕ Add New Company")

    with st.form("add_company_form", clear_on_submit=True):

        st.markdown("**Company Information**")

        r1, r2 = st.columns(2)

        with r1:
            name = st.text_input("Company Name *")

            industry = st.text_input(
                "Industry",
                placeholder="e.g. IT/Software, Healthcare, Finance"
            )

        with r2:
            website = st.text_input(
                "Website",
                placeholder="https://company.com"
            )

            address = st.text_area("Address", height=70)

        st.markdown("---")
        st.markdown("**Contact Details**")

        c1, c2, c3 = st.columns(3)

        with c1:
            contact_person = st.text_input("Contact Person")

        with c2:
            contact_email = st.text_input("Contact Email")

        with c3:
            contact_phone = st.text_input("Contact Phone")

        submitted = st.form_submit_button(
            "➕ Add Company",
            type="primary",
            use_container_width=True
        )

        if submitted:

            if not name:
                st.error("Company name is required.")

            else:

                with get_db() as db:

                    existing = db.query(Company).filter(
                        Company.name == name.strip()
                    ).first()

                    if existing:
                        st.error(
                            f"Company '{name}' already exists."
                        )

                    else:

                        comp = Company(
                            name=name.strip(),
                            industry=industry.strip(),
                            website=website.strip(),
                            address=address.strip(),
                            contact_person=contact_person.strip(),
                            contact_email=contact_email.strip(),
                            contact_phone=contact_phone.strip(),
                        )

                        db.add(comp)
                        db.commit()

                st.success(
                    f"✅ Company **{name}** added successfully!"
                )

                st.rerun()