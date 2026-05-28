"""
Invoice Generator UI
CRM
"""

import streamlit as st
from datetime import date
from database.connection import get_db
from database.models import Candidate, Company, Recruiter, User
from app.utils.invoice_generator import generate_invoice_pdf, generate_invoice_number


def render_invoice_generator():
    st.markdown("### 🧾 Generate Tax Invoice")
    st.markdown("Generate a GST invoice in standard format for any candidate.")

    # ── Step 1: Select Candidate ──────────────────
    st.markdown("**Step 1 — Select Candidate**")

    with get_db() as db:
        candidates_raw = (
            db.query(Candidate, Company.name.label("company_name"))
            .outerjoin(Company, Candidate.company_id == Company.id)
            .filter(Candidate.joining_date.isnot(None))
            .order_by(Candidate.name)
            .all()
        )
        candidates_data = []
        for row in candidates_raw:
            c = row.Candidate
            candidates_data.append({
                "id": c.id,
                "candidate_id": c.candidate_id,
                "name": c.name,
                "phone": c.phone,
                "designation": c.designation or "",
                "joining_date": c.joining_date,
                "payment_amount": float(c.payment_amount or 0),
                "company_id": c.company_id,
                "company_name": row.company_name or "",
                "invoice_number": c.invoice_number or "",
            })

        # Get companies for address lookup
        companies_raw = db.query(Company).all()
        company_details = {
            c.id: {
                "name": c.name,
                "address": c.address or "",
                "gstin": c.contact_email or "",
                "phone": c.contact_phone or "",
                "contact": c.contact_person or "",
            }
            for c in companies_raw
        }

    if not candidates_data:
        st.warning("No candidates with joining dates found. Please add joining dates to candidates first.")
        return

    # Candidate selector
    cand_options = {f"{c['name']} — {c['candidate_id']} ({c['company_name']})": c for c in candidates_data}
    selected_label = st.selectbox("Select Candidate", list(cand_options.keys()))
    selected = cand_options[selected_label]

    st.markdown("---")

    # ── Step 2: Invoice Details ────────────────────
    st.markdown("**Step 2 — Invoice Details**")

    col1, col2 = st.columns(2)
    with col1:
        invoice_seq = st.number_input("Invoice Sequence Number", min_value=1, value=1, step=1)
        invoice_number = generate_invoice_number(invoice_seq)
        st.info(f"Invoice Number: **{invoice_number}**")

    with col2:
        invoice_date = st.date_input("Invoice Date", value=date.today())

    st.markdown("---")

    # ── Step 3: Company Details ────────────────────
    st.markdown("**Step 3 — Company (Client) Details**")

    comp = company_details.get(selected["company_id"], {})
    c1, c2 = st.columns(2)
    with c1:
        company_name = st.text_input("Company Name *", value=selected["company_name"])
        company_address = st.text_area("Company Address", value=comp.get("address", ""), height=80,
                                        placeholder="Full address with city, state, pincode")
        company_gstin = st.text_input("Company GSTIN", value="", placeholder="e.g. 06AADCD4946L2ZD")
    with c2:
        company_pan = st.text_input("Company PAN", placeholder="e.g. AADCD4946L")
        company_state = st.text_input("State", value="Haryana")
        place_of_supply = st.text_input("Place of Supply", placeholder="e.g. GURUGRAM")

    st.markdown("---")

    # ── Step 4: Candidate & Amount ─────────────────
    st.markdown("**Step 4 — Candidate & Amount**")

    c1, c2, c3 = st.columns(3)
    with c1:
        candidate_name = st.text_input("Candidate Name *", value=selected["name"])
    with c2:
        designation = st.text_input("Designation / Process", value=selected["designation"])
    with c3:
        joining_date = st.date_input("Date of Joining", value=selected["joining_date"])

    c4, c5, c6 = st.columns(3)
    with c4:
        base_amount = st.number_input(
            "Base Amount (₹) *",
            min_value=0.0,
            step=1000.0,
            value=selected["payment_amount"] if selected["payment_amount"] > 0 else 0.0
        )
    with c5:
        apply_igst = st.checkbox("Apply IGST @ 18%", value=True)
    with c6:
        authorized_signatory = st.text_input("Authorized Signatory", value="Himanshu Malik")

    # Live calculation
    igst_amount = round(base_amount * 18 / 100) if apply_igst else 0
    total_amount = base_amount + igst_amount

    if base_amount > 0:
        st.markdown(f"""
        <div style="background:#1E293B; border:1px solid #334155; border-radius:10px; padding:1rem 1.5rem; margin:1rem 0;">
            <div style="display:flex; gap:2rem; flex-wrap:wrap;">
                <div>
                    <div style="font-size:0.75rem; color:#64748B; margin-bottom:2px;">Base Amount</div>
                    <div style="font-size:1.2rem; font-weight:700; color:#F1F5F9;">₹{base_amount:,.0f}</div>
                </div>
                <div>
                    <div style="font-size:0.75rem; color:#64748B; margin-bottom:2px;">IGST @ 18%</div>
                    <div style="font-size:1.2rem; font-weight:700; color:#F59E0B;">₹{igst_amount:,.0f}</div>
                </div>
                <div>
                    <div style="font-size:0.75rem; color:#64748B; margin-bottom:2px;">Total Payable</div>
                    <div style="font-size:1.4rem; font-weight:800; color:#10B981;">₹{total_amount:,.0f}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Step 5: Signature Upload ───────────────────
    st.markdown("**Step 5 — Signature (Optional)**")
    st.caption("Upload a signature image to appear on the invoice. PNG with transparent background works best.")

    signature_file = st.file_uploader(
        "Upload Signature Image",
        type=["png", "jpg", "jpeg"],
        help="Recommended: PNG with transparent background, max 2MB"
    )

    signature_bytes = None
    if signature_file is not None:
        signature_bytes = signature_file.read()
        st.image(signature_bytes, caption="Signature Preview", width=200)

    st.markdown("---")

    # ── Generate Button ────────────────────────────
    if st.button("🧾 Generate Invoice PDF", type="primary", use_container_width=True):
        if not candidate_name or not company_name or base_amount <= 0:
            st.error("Please fill Candidate Name, Company Name and Amount.")
        else:
            with st.spinner("Generating invoice..."):
                invoice_data = {
                    "invoice_number": invoice_number,
                    "invoice_date": invoice_date,
                    "candidate_name": candidate_name,
                    "candidate_designation": designation,
                    "joining_date": joining_date,
                    "company_name": company_name,
                    "company_address": company_address,
                    "company_gstin": company_gstin,
                    "company_state": company_state,
                    "company_pan": company_pan,
                    "place_of_supply": place_of_supply,
                    "amount": base_amount,
                    "apply_igst": apply_igst,
                    "authorized_signatory": authorized_signatory,
                    "signature_image": signature_bytes,   # ← NEW
                }
                pdf_bytes = generate_invoice_pdf(invoice_data)

            # Save invoice number to candidate record
            with get_db() as db:
                cand = db.query(Candidate).filter(Candidate.id == selected["id"]).first()
                if cand:
                    cand.invoice_number = invoice_number
                    cand.invoice_date = invoice_date

            filename = f"Invoice_{invoice_number.replace('/', '_')}_{candidate_name.replace(' ', '_')}.pdf"
            st.download_button(
                label="⬇️ Download Invoice PDF",
                data=pdf_bytes,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True,
            )
            st.success(f"✅ Invoice {invoice_number} generated successfully!")
            st.info(f"📋 Invoice number saved to candidate record: {selected['candidate_id']}")