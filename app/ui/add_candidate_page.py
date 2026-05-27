"""
Add / Edit Candidate Page
BLACKWOODS CRM
"""

import streamlit as st
import pandas as pd
from datetime import date
from database.connection import get_db
from database.models import Candidate, Company, Recruiter, User, CandidateStatus, PaymentStatus
from app.candidates.candidate_service import (
    create_candidate, update_candidate, bulk_import_candidates
)
from app.auth.auth import get_current_user
from app.utils.whatsapp import get_whatsapp_url, get_all_templates, get_template_message


def render_add_candidate():
    is_edit = "editing_candidate_id" in st.session_state and st.session_state.editing_candidate_id

    if is_edit:
        st.markdown("""
        <div class="page-title">✏️ Edit Candidate</div>
        <div class="page-subtitle">Update candidate information and status.</div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="page-title">➕ Add New Candidate</div>
        <div class="page-subtitle">Register a new candidate in the recruitment pipeline.</div>
        """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📝 Candidate Form", "📤 Bulk Import (Excel)"])

    with tab1:
        _render_candidate_form(is_edit)

    with tab2:
        _render_bulk_import()


def _get_dropdown_data():
    with get_db() as db:
        companies = db.query(Company).filter(Company.is_active == True).order_by(Company.name).all()
        recruiters = (
            db.query(Recruiter, User.full_name)
            .join(User, Recruiter.user_id == User.id)
            .filter(Recruiter.is_active == True)
            .all()
        )
        company_map = {c.name: c.id for c in companies}
        recruiter_map = {u_name: r.id for r, u_name in recruiters}
    return company_map, recruiter_map


def _render_candidate_form(is_edit: bool):
    user = get_current_user()
    company_map, recruiter_map = _get_dropdown_data()

    existing_data = {}
    existing_company = None
    existing_recruiter = None

    if is_edit:
        with get_db() as db:
            cand = db.query(Candidate).filter(
                Candidate.id == st.session_state.editing_candidate_id
            ).first()
            if cand:
                existing_data = {
                    "name": cand.name or "",
                    "phone": cand.phone or "",
                    "alternate_phone": cand.alternate_phone or "",
                    "email": cand.email or "",
                    "designation": cand.designation or "",
                    "ctc": float(cand.ctc or 0),
                    "selection_date": cand.selection_date,
                    "expected_joining_date": cand.expected_joining_date,
                    "joining_date": cand.joining_date,
                    "status": cand.status.value if cand.status else "Selected",
                    "payment_status": cand.payment_status.value if cand.payment_status else "Pending",
                    "payment_amount": float(cand.payment_amount or 0),
                    "payment_received_date": cand.payment_received_date,
                    "invoice_number": cand.invoice_number or "",
                    "invoice_date": cand.invoice_date,
                    "notes": cand.notes or "",
                    "drop_reason": cand.drop_reason or "",
                }
                if cand.company_id:
                    comp = db.query(Company).filter(Company.id == cand.company_id).first()
                    existing_company = comp.name if comp else None
                if cand.recruiter_id:
                    rec = (
                        db.query(Recruiter, User.full_name)
                        .join(User, Recruiter.user_id == User.id)
                        .filter(Recruiter.id == cand.recruiter_id)
                        .first()
                    )
                    existing_recruiter = rec[1] if rec else None

        if not existing_data:
            st.error("Candidate not found.")
            return

    with st.form("candidate_form", clear_on_submit=False):
        st.markdown("**👤 Personal Information**")
        r1c1, r1c2, r1c3 = st.columns(3)
        with r1c1:
            name = st.text_input("Full Name *", value=existing_data.get("name", ""))
        with r1c2:
            phone = st.text_input("Phone Number *", value=existing_data.get("phone", ""))
        with r1c3:
            alt_phone = st.text_input("Alternate Phone", value=existing_data.get("alternate_phone", ""))

        r2c1, r2c2 = st.columns(2)
        with r2c1:
            email = st.text_input("Email Address", value=existing_data.get("email", ""))
        with r2c2:
            designation = st.text_input("Designation / Role", value=existing_data.get("designation", ""))

        st.markdown("---")
        st.markdown("**🏢 Placement Information**")

        p1, p2, p3 = st.columns(3)
        with p1:
            company_names = ["— Select Company —"] + list(company_map.keys())
            company_default = company_names.index(existing_company) if existing_company in company_names else 0
            company_sel = st.selectbox("Company", company_names, index=company_default)
        with p2:
            recruiter_names = ["— Select Recruiter —"] + list(recruiter_map.keys())
            rec_default = recruiter_names.index(existing_recruiter) if existing_recruiter in recruiter_names else 0
            recruiter_sel = st.selectbox("Recruiter", recruiter_names, index=rec_default)
        with p3:
            ctc = st.number_input("CTC (Annual, ₹)", min_value=0.0, step=10000.0,
                                  value=existing_data.get("ctc", 0.0))

        d1, d2, d3 = st.columns(3)
        with d1:
            selection_date = st.date_input("Selection Date",
                                           value=existing_data.get("selection_date", date.today()))
        with d2:
            expected_joining = st.date_input("Expected Joining Date",
                                             value=existing_data.get("expected_joining_date", None))
        with d3:
            joining_date = st.date_input("Actual Joining Date",
                                         value=existing_data.get("joining_date", None))

        st.markdown("---")
        st.markdown("**💰 Status & Payment**")

        sp1, sp2, sp3, sp4 = st.columns(4)
        with sp1:
            status_options = [s.value for s in CandidateStatus]
            current_status = existing_data.get("status", "Interview Scheduled")
            status_default = status_options.index(current_status) if current_status in status_options else 0
            status = st.selectbox("Candidate Status", status_options, index=status_default)
        with sp2:
            payment_options = [p.value for p in PaymentStatus]
            current_pay = existing_data.get("payment_status", "Pending")
            pay_default = payment_options.index(current_pay) if current_pay in payment_options else 0
            payment_status = st.selectbox("Payment Status", payment_options, index=pay_default)
        with sp3:
            payment_amount = st.number_input("Placement Fee (₹)", min_value=0.0, step=1000.0,
                                             value=existing_data.get("payment_amount", 0.0))
        with sp4:
            payment_received_date = st.date_input("Payment Received Date",
                                                   value=existing_data.get("payment_received_date", None))

        inv1, inv2 = st.columns(2)
        with inv1:
            invoice_number = st.text_input("Invoice Number", value=existing_data.get("invoice_number", ""))
        with inv2:
            invoice_date = st.date_input("Invoice Date", value=existing_data.get("invoice_date", None))

        st.markdown("---")
        st.markdown("**📝 Notes & Remarks**")
        notes = st.text_area("Notes", value=existing_data.get("notes", ""), height=100)

        if is_edit and existing_data.get("status") == "Drop":
            drop_reason = st.text_area("Drop Reason", value=existing_data.get("drop_reason", ""), height=80)
        else:
            drop_reason = ""

        st.markdown("<br>", unsafe_allow_html=True)

        sb1, sb2, sb3 = st.columns([1, 1, 3])
        with sb1:
            submitted = st.form_submit_button("💾 Save Candidate", type="primary", use_container_width=True)
        with sb2:
            if is_edit and st.form_submit_button("✖ Cancel Edit", use_container_width=True):
                st.session_state.show_edit_form = False
                st.session_state.editing_candidate_id = None
                st.session_state.current_page = "Candidates"
                st.rerun()

        if submitted:
            if not name or not phone:
                st.error("Name and Phone are required.")
            else:
                data = {
                    "name": name.strip(),
                    "phone": phone.strip(),
                    "alternate_phone": alt_phone.strip(),
                    "email": email.strip(),
                    "company_id": company_map.get(company_sel),
                    "recruiter_id": recruiter_map.get(recruiter_sel),
                    "designation": designation.strip(),
                    "ctc": ctc,
                    "selection_date": selection_date,
                    "expected_joining_date": expected_joining,
                    "joining_date": joining_date,
                    "status": status,
                    "payment_status": payment_status,
                    "payment_amount": payment_amount,
                    "payment_received_date": payment_received_date,
                    "invoice_number": invoice_number.strip(),
                    "invoice_date": invoice_date,
                    "notes": notes.strip(),
                    "drop_reason": drop_reason,
                }

                if is_edit:
                    ok, msg = update_candidate(
                        st.session_state.editing_candidate_id, data, user["full_name"]
                    )
                    if ok:
                        st.success(f"✅ {msg}")
                        st.session_state.show_edit_form = False
                        st.session_state.editing_candidate_id = None
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
                else:
                    ok, msg, cid = create_candidate(data, user["full_name"])
                    if ok:
                        st.success(f"✅ {msg}")
                        st.balloons()
                    else:
                        st.error(f"❌ {msg}")

    # WhatsApp Section (Edit Mode only)
    if is_edit and existing_data:
        st.markdown("---")
        st.markdown("**💬 WhatsApp Messaging**")
        wa_col1, wa_col2 = st.columns([1, 2])
        with wa_col1:
            templates = get_all_templates()
            template_labels = [t["label"] for t in templates]
            selected_template_idx = st.selectbox(
                "Message Template", range(len(templates)),
                format_func=lambda i: template_labels[i]
            )
            selected_template = templates[selected_template_idx]["key"]
        with wa_col2:
            filled_msg = get_template_message(
                selected_template,
                name=existing_data.get("name", ""),
                company=existing_company or "Your Company",
                joining_date=str(existing_data.get("expected_joining_date") or existing_data.get("joining_date") or "TBD"),
                designation=existing_data.get("designation") or "the role",
                amount=f"{existing_data.get('payment_amount', 0):,.0f}",
            )
            wa_link = get_whatsapp_url(existing_data.get("phone", ""), filled_msg)
            st.markdown(f"""
            <a href="{wa_link}" target="_blank" style="display:inline-flex;align-items:center;gap:6px;
            background:#25D366;color:white;padding:0.6rem 1.25rem;border-radius:999px;
            font-size:0.9rem;font-weight:600;text-decoration:none;">
            💬 Open WhatsApp Chat</a>
            """, unsafe_allow_html=True)
            st.text_area("Message Preview", value=filled_msg, height=150, disabled=True)


def _render_bulk_import():
    import re
    from datetime import datetime as dt

    st.info("📤 Upload your Blackwoods Excel file — all monthly sheets will be imported automatically.")

    uploaded = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])

    if uploaded:
        def parse_date(date_str):
            try:
                if not date_str or pd.isna(date_str):
                    return None
            except Exception:
                pass
            date_str = str(date_str).strip()
            date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str, flags=re.IGNORECASE)
            date_str = date_str.strip()
            formats = ['%d %B %Y', '%d %b %Y', '%d %B', '%d %b']
            for fmt in formats:
                try:
                    d = dt.strptime(date_str, fmt)
                    if d.year == 1900:
                        d = d.replace(year=dt.now().year)
                    return d.date()
                except:
                    continue
            return None

        def clean_phone(phone):
            try:
                if not phone or pd.isna(phone):
                    return ""
            except Exception:
                pass
            phone = str(phone).strip()
            # Remove all non-digit characters
            phone = re.sub(r'\D', '', phone)
            # Remove leading 91 (country code)
            if phone.startswith('91') and len(phone) == 12:
                phone = phone[2:]
            # Remove leading 0
            if phone.startswith('0') and len(phone) == 11:
                phone = phone[1:]
            # Return if valid 10 digit number
            if len(phone) == 10:
                return phone
            # If longer, take last 10 digits
            if len(phone) > 10:
                return phone[-10:]
            # Return whatever we have if short
            return phone if phone else ""

        def map_status(s):
            try:
                if not s or pd.isna(s): return 'Selected'
            except Exception:
                pass
            if not s: return 'Selected'
            s = str(s).strip().lower()
            if 'drop' in s: return 'Drop'
            if 'paid' in s: return 'Payment Received'
            if 'join' in s: return 'Joined'
            return 'Selected'

        def map_payment(s):
            try:
                if not s or pd.isna(s): return 'Pending'
            except Exception:
                pass
            if not s: return 'Pending'
            s = str(s).strip().lower()
            if s == 'paid': return 'Received'
            return 'Pending'

        try:
            import openpyxl
            import io
            file_bytes = uploaded.read()
            xl = {}
            wb = None
            for kwargs in [
                {"data_only": True, "keep_links": False},
                {"data_only": True, "keep_links": False, "keep_vba": False},
                {"data_only": True},
            ]:
                try:
                    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), **kwargs)
                    break
                except Exception:
                    continue
            if wb is None:
                st.error("Could not open the Excel file. Please re-save it in Excel and try again.")
                return
            for sheet in wb.sheetnames:
                try:
                    ws = wb[sheet]
                    data = list(ws.values)
                    if not data:
                        continue
                    cols_raw = data[0]
                    cols = [str(c).strip() if c is not None and str(c).strip() not in ['', 'None'] else f"col_{i}" for i, c in enumerate(cols_raw)]
                    rows = []
                    for row in data[1:]:
                        rows.append([str(v).strip() if v is not None else "" for v in row])
                    xl[sheet] = pd.DataFrame(rows, columns=cols)
                except Exception:
                    continue
        except Exception as e:
            st.error(f"Error reading file: {e}")
            return

        all_records = []
        sheet_summary = []

        for sheet_name, df in xl.items():
            if sheet_name.strip().lower() == 'collective data':
                continue
            df = df.dropna(how='all')
            df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]
            sheet_count = 0

            for _, row in df.iterrows():
                name_col = next((c for c in df.columns if c.startswith('name')), None)
                name = str(row.get(name_col, '')).strip()
                if not name or name.lower() in ['nan', 'none', '']:
                    continue

                phone_col = next((c for c in df.columns if 'number' in c), None)
                phone = clean_phone(row.get(phone_col, '')) if phone_col else ''
                if not phone or len(phone) < 8:
                    phone = '0000000000'

                company_col = next((c for c in df.columns if 'company' in c), None)
                company = str(row.get(company_col, '')).strip() if company_col else ''
                if company.lower() in ['nan', 'none']: company = ''

                process_col = next((c for c in df.columns if 'process' in c or 'procecss' in c), None)
                process = str(row.get(process_col, '')).strip() if process_col else ''
                if process.lower() in ['nan', 'none']: process = ''

                rec_col = next((c for c in df.columns if 'recruiter' in c), None)
                recruiter = str(row.get(rec_col, '')).strip() if rec_col else ''
                if recruiter.lower() in ['nan', 'none']: recruiter = ''

                date_col = next((c for c in df.columns if 'selection' in c), None)
                sel_date = parse_date(row.get(date_col, '')) if date_col else None

                join_col = next((c for c in df.columns if 'joining' in c or 'doj' in c), None)
                join_date = parse_date(row.get(join_col, '')) if join_col else None

                status_col = next((c for c in df.columns if 'status' in c), None)
                status = map_status(row.get(status_col, '')) if status_col else 'Selected'

                pay_col = next((c for c in df.columns if 'payout' in c or 'pay_out' in c), None)
                payment_status = map_payment(row.get(pay_col, '')) if pay_col else 'Pending'

                all_records.append({
                    'name': name,
                    'phone': phone,
                    'company': company,
                    'designation': process,
                    'recruiter_name': recruiter,
                    'selection_date': sel_date,
                    'joining_date': join_date,
                    'status': status,
                    'payment_status': payment_status,
                    'source_sheet': sheet_name,
                })
                sheet_count += 1

            sheet_summary.append(f"✅ {sheet_name}: {sheet_count} candidates")

        st.markdown(f"### 📊 Found **{len(all_records)} candidates** across {len(sheet_summary)} sheets")
        for s in sheet_summary:
            st.markdown(f"- {s}")

        st.markdown("**Preview (first 10):**")
        preview = pd.DataFrame(all_records[:10])[['name', 'phone', 'company', 'recruiter_name', 'status', 'payment_status', 'source_sheet']]
        st.dataframe(preview, use_container_width=True, hide_index=True)

        st.markdown("---")
        if st.button("🚀 Import All Candidates", type="primary", use_container_width=True):
            from database.connection import get_db_session
            from database.models import CandidateStatus as CS, PaymentStatus as PS

            progress = st.progress(0)
            status_text = st.empty()
            success = 0
            failed = 0
            skipped = 0

            session = get_db_session()
            companies_cache = {c.name.lower(): c.id for c in session.query(Company).all()}
            recruiters_cache = {}
            for r, uname in session.query(Recruiter, User.full_name).join(User, Recruiter.user_id == User.id).all():
                recruiters_cache[uname.lower()] = r.id
            last = session.query(Candidate).order_by(Candidate.id.desc()).first()
            counter = (last.id + 1000) if last else 1000
            session.close()

            total = len(all_records)

            for i, rec in enumerate(all_records):
                session = get_db_session()
                try:
                    phone = rec['phone']
                    # Check duplicate by phone
                    if phone != '0000000000':
                        if session.query(Candidate).filter(Candidate.phone == phone).first():
                            skipped += 1
                            session.close()
                            continue
                    # Check duplicate by name for 0000000000 phones
                    else:
                        existing_name = session.query(Candidate).filter(
                            Candidate.name == rec['name'],
                            Candidate.notes.like(f"%{rec['source_sheet']}%")
                        ).first()
                        if existing_name:
                            skipped += 1
                            session.close()
                            continue

                    company_id = None
                    if rec['company']:
                        comp_key = rec['company'].lower()
                        for cached_name, cached_id in companies_cache.items():
                            if comp_key[:8] in cached_name or cached_name[:8] in comp_key:
                                company_id = cached_id
                                break
                        if not company_id:
                            new_comp = Company(name=rec['company'], is_active=True)
                            session.add(new_comp)
                            session.flush()
                            company_id = new_comp.id
                            companies_cache[rec['company'].lower()] = company_id

                    recruiter_id = None
                    if rec['recruiter_name']:
                        rec_key = rec['recruiter_name'].lower()
                        for cached_name, cached_id in recruiters_cache.items():
                            if rec_key in cached_name or cached_name in rec_key:
                                recruiter_id = cached_id
                                break

                    counter += 1
                    cid = f"CND{str(counter).zfill(5)}"
                    while session.query(Candidate).filter(Candidate.candidate_id == cid).first():
                        counter += 1
                        cid = f"CND{str(counter).zfill(5)}"

                    try:
                        status_val = CS(rec['status'])
                    except:
                        status_val = CS.SELECTED

                    try:
                        pay_val = PS(rec['payment_status'])
                    except:
                        pay_val = PS.PENDING

                    is_eligible = False
                    if rec['joining_date']:
                        days = (date.today() - rec['joining_date']).days
                        is_eligible = days >= 90

                    candidate = Candidate(
                        candidate_id=cid,
                        name=rec['name'],
                        phone=rec['phone'],
                        company_id=company_id,
                        recruiter_id=recruiter_id,
                        designation=rec['designation'],
                        selection_date=rec['selection_date'],
                        joining_date=rec['joining_date'],
                        status=status_val,
                        payment_status=pay_val,
                        is_90_day_eligible=is_eligible,
                        notes=f"Imported from: {rec['source_sheet']}",
                    )
                    session.add(candidate)
                    session.commit()
                    success += 1

                except Exception as e:
                    session.rollback()
                    failed += 1
                finally:
                    session.close()

                progress.progress((i + 1) / total)
                status_text.markdown(f"Processing {i+1}/{total} — ✅ {success} imported, ⏭ {skipped} skipped, ❌ {failed} failed")

            progress.progress(1.0)
            st.success(f"✅ Done! {success} imported, {skipped} skipped, {failed} failed")
            st.balloons()