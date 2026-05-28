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
    import io
    from datetime import datetime as dt
    from difflib import SequenceMatcher

    # ── CRM field → all known column name variants ─────────────
    SYNONYMS = {
        "name": [
            "name", "full name", "candidate name", "applicant name", "applicant",
            "person", "candidate", "employee name", "emp name",
        ],
        "phone": [
            "phone", "mobile", "number", "contact", "ph", "mob", "cell",
            "whatsapp", "phone no", "mobile no", "contact no",
            "phone number", "mobile number", "contact number", "ph no",
        ],
        "company": [
            "company", "organisation", "organization", "client", "employer",
            "firm", "company name", "client name", "employer name",
            "hiring company", "client company",
        ],
        "designation": [
            "designation", "process", "procecss", "role", "position",
            "job title", "post", "profile", "job role", "job profile",
            "dept", "department", "vertical", "campaign",
        ],
        "recruiter_name": [
            "recruiter", "recruiter name", "rec", "sourced by", "consultant",
            "hired by", "bdm", "account manager", "spoc", "rm",
        ],
        "selection_date": [
            "selection", "selected on", "select date", "date of selection",
            "dos", "selection date", "date selected", "joining month",
        ],
        "joining_date": [
            "joining", "doj", "date of joining", "join date", "joining date",
            "actual joining", "date joined", "joining month",
        ],
        "status": [
            "status", "stage", "current status", "pipeline",
            "candidate status", "emp status",
        ],
        "payment_status": [
            "payout", "pay out", "payment", "payment status",
            "pay status", "invoice status", "billing status", "pay out",
        ],
    }

    # Column names that are salary/finance — never map to text fields
    NUMERIC_KEYWORDS = [
        "ctc", "salary", "package", "lpa", "lakh", "annual", "gross", "net",
        "fee", "commission", "amount", "cost", "inr", "rs ", "rupee",
        "offered", "fixed", "variable", "incentive", "bonus", "wage",
    ]
    TEXT_ONLY_FIELDS = {"name", "company", "designation", "recruiter_name"}

    # ── Status values from client files → CRM status values ────
    # These map ALL the creative ways hiring companies label statuses
    STATUS_MAP = {
        # Active / in pipeline → Selected
        "active": "Selected",
        "selected": "Selected",
        "shortlisted": "Selected",
        "in process": "Selected",
        "offered": "Selected",
        "pending": "Selected",
        "yet to join": "Selected",
        "not joined": "Selected",
        "": "Selected",
        # Joined
        "joined": "Joined",
        "on board": "Joined",
        "onboard": "Joined",
        "onboarded": "Joined",
        "working": "Joined",
        "confirmed": "Joined",
        # Drop
        "drop": "Drop",
        "dropout": "Drop",
        "no show": "Drop",
        "no-show": "Drop",
        "not joined": "Drop",
        "absconded": "Drop",
        "rejected": "Drop",
        "declined": "Drop",
        "withdrew": "Drop",
        "replace": "Drop",
        # Payment received
        "paid": "Payment Received",
        "payment done": "Payment Received",
        "invoice paid": "Payment Received",
    }

    # Payout column values — can encode EITHER status OR payment_status
    PAYOUT_AS_PAYMENT = {
        "paid": "Received",
        "unpaid": "Pending",
        "not paid": "Pending",
        "pending": "Pending",
        "due": "Pending",
        "invoice raised": "Pending",
    }
    # Payout values that actually mean STATUS not payment
    PAYOUT_IS_STATUS = {"drop", "dropout", "replace", "no show", "absconded"}

    def _norm(s):
        return re.sub(r"[^a-z0-9 ]", " ", str(s).lower()).strip()

    def _score(col, syn):
        cn, sn = _norm(col), _norm(syn)
        ratio = SequenceMatcher(None, cn, sn).ratio()
        if sn in cn or cn in sn:
            ratio = max(ratio, 0.85)
        return ratio

    def _looks_like_phone_header(val):
        """Return True if a header cell looks like a phone number (leaked into headers)."""
        if val is None:
            return False
        s = re.sub(r"[\s\(\)\-\+]", "", str(val))
        digits = re.sub(r"\D", "", s)
        return len(digits) >= 8 and len(digits) <= 13

    def _is_numeric_col(col_name, series):
        """True if column name implies salary/finance OR data is mostly large numbers."""
        n = _norm(col_name)
        for kw in NUMERIC_KEYWORDS:
            if kw in n:
                return True
        try:
            nums = pd.to_numeric(series.dropna(), errors="coerce").dropna()
            if len(nums) == 0:
                return False
            if (len(nums) / max(len(series.dropna()), 1)) > 0.6 and nums.median() > 1000:
                return True
        except Exception:
            pass
        return False

    def detect_columns(cols, df_sample):
        """
        Global best-score assignment:
        1. Build full (field × col) score matrix
        2. Block numeric/salary cols from text-only fields
        3. Assign highest-score pairs first, no reuse of col or field
        4. Threshold 0.72 — high enough to avoid false positives
        """
        scores = {}
        for field, syns in SYNONYMS.items():
            for col in cols:
                best = max(_score(col, syn) for syn in syns)
                if field in TEXT_ONLY_FIELDS:
                    series = df_sample[col] if col in df_sample.columns else pd.Series()
                    if _is_numeric_col(col, series):
                        best = 0.0
                scores[(field, col)] = best

        mapping = {}
        used_cols = set()
        for (field, col), score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            if score < 0.72:
                break
            if field in mapping or col in used_cols:
                continue
            mapping[field] = col
            used_cols.add(col)
        return mapping

    def safe_val(v):
        try:
            if v is None:
                return ""
            s = str(v).strip()
            return "" if s.lower() in ["nan", "none", "nat", ""] else s
        except Exception:
            return ""

    def parse_date(val):
        s = safe_val(val)
        if not s:
            return None
        s = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", s, flags=re.IGNORECASE).strip()
        for fmt in ["%d %B %Y", "%d %b %Y", "%Y-%m-%d", "%d/%m/%Y",
                    "%m/%d/%Y", "%d-%m-%Y", "%d %B", "%d %b", "%B %Y", "%b %Y"]:
            try:
                d = dt.strptime(s, fmt)
                # Month-only formats (no day) → use 1st of that month
                if fmt in ("%B %Y", "%b %Y"):
                    return d.date()
                return d.replace(year=dt.now().year).date() if d.year == 1900 else d.date()
            except Exception:
                continue
        return None

    def clean_phone(val):
        s = safe_val(val)
        if not s:
            return ""
        s = re.sub(r"\D", "", s)
        # Strip negative sign artifact (Excel stores phone as negative number)
        s = s.lstrip("-")
        if s.startswith("91") and len(s) == 12:
            s = s[2:]
        if s.startswith("0") and len(s) == 11:
            s = s[1:]
        return s[-10:] if len(s) >= 10 else s

    def resolve_status(status_val, payout_val):
        """
        Intelligently resolve CRM status from whatever the client file provides.
        Some sheets have no Status column — status must be inferred from Payout.
        Some Payout values are actually status signals (Drop, Replace).
        """
        sv = _norm(safe_val(status_val))
        pv = _norm(safe_val(payout_val))

        # If explicit status column has a value, use it
        if sv:
            for key, crm_val in STATUS_MAP.items():
                if key and key in sv:
                    return crm_val
            return "Selected"

        # No status column — infer from payout
        if pv in PAYOUT_IS_STATUS:
            return "Drop"
        if "join" in pv:
            return "Joined"
        # Empty payout or payment-only values → still Selected
        return "Selected"

    def resolve_payment(payout_val, status_val):
        """
        Resolve payment status.
        Skip if payout value is actually a status signal.
        Numeric payout values = amount, not status → default Pending.
        """
        pv = _norm(safe_val(payout_val))
        if not pv:
            return "Pending"
        # Payout value is a status, not a payment
        if pv in PAYOUT_IS_STATUS:
            return "Pending"
        # Numeric value = payout amount, not payment status
        if re.match(r"^\d+(\.\d+)?$", pv.replace(" ", "")):
            return "Pending"
        for key, crm_val in PAYOUT_AS_PAYMENT.items():
            if key in pv:
                return crm_val
        return "Pending"

    # ═══════════════════════════════════════════════════════════
    # UI
    # ═══════════════════════════════════════════════════════════
    st.info(
        "📤 Upload any Excel or CSV file — the system auto-detects columns regardless of format. "
        "Review the mapping below and fix anything before importing."
    )

    # ── Data source selector ───────────────────────────────────
    st.markdown("### 📋 Who is providing this data?")
    data_source = st.radio(
        "Select data source",
        options=["🏢 Sent by Hiring Company", "🗂️ Our Internal Database"],
        horizontal=True,
        key="bulk_data_source",
        help=(
            "Hiring Company: file sent by the client — system will auto-assign all candidates to that company.\n"
            "Internal Database: our own records — company is taken from the file per candidate."
        )
    )
    is_company_file = data_source == "🏢 Sent by Hiring Company"

    # If hiring company file — ask which company
    forced_company_id = None
    forced_company_name = None
    if is_company_file:
        with get_db() as db:
            companies = db.query(Company).filter(Company.is_active == True).order_by(Company.name).all()
            company_map = {c.name: c.id for c in companies}

        company_names = list(company_map.keys())
        col_comp, col_new = st.columns([3, 1])
        with col_comp:
            selected_company = st.selectbox(
                "Select the hiring company that sent this file",
                options=["— select company —"] + company_names,
                key="bulk_forced_company"
            )
        with col_new:
            st.markdown("<br>", unsafe_allow_html=True)
            add_new = st.checkbox("Add new company", key="bulk_add_new_company")

        if add_new:
            new_company_name = st.text_input("New company name", key="bulk_new_company_name")
            if new_company_name.strip():
                forced_company_name = new_company_name.strip()
                st.success(f"Will create and use: **{forced_company_name}**")
        elif selected_company != "— select company —":
            forced_company_name = selected_company
            forced_company_id = company_map[selected_company]
            st.success(f"All candidates will be assigned to: **{forced_company_name}**")
        else:
            st.warning("Please select a company before uploading.")
            return

    uploaded = st.file_uploader("Upload Excel / CSV File", type=["xlsx", "xls", "csv"])
    if not uploaded:
        return

    # ── Read file ──────────────────────────────────────────────
    try:
        if uploaded.name.endswith(".csv"):
            xl = {"CSV": pd.read_csv(uploaded)}
        else:
            import openpyxl
            file_bytes = uploaded.read()
            wb = None
            for kwargs in [{"data_only": True, "keep_links": False}, {"data_only": True}]:
                try:
                    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), **kwargs)
                    break
                except Exception:
                    continue
            if wb is None:
                st.error("Could not open the Excel file. Please re-save it and try again.")
                return

            xl = {}
            for sheet in wb.sheetnames:
                try:
                    ws = wb[sheet]
                    data = list(ws.values)
                    if not data:
                        continue

                    cols_raw = list(data[0])

                    # ── Fix: detect phone numbers leaked into header row ──
                    # (e.g. April sheet where col[1] = -7068217575)
                    for i, c in enumerate(cols_raw):
                        if _looks_like_phone_header(c):
                            # Scan nearby cols to guess what this should have been
                            cols_raw[i] = "Number"

                    # ── Fix: detect two tables side-by-side (December) ──
                    # If duplicate column names exist, split at the first duplicate
                    seen = {}
                    split_at = None
                    clean_cols = []
                    for i, c in enumerate(cols_raw):
                        label = str(c).strip() if c is not None and str(c).strip() not in ["", "None"] else f"col_{i}"
                        if label in seen and split_at is None and label != f"col_{i}":
                            split_at = i
                            break
                        seen[label] = i
                        clean_cols.append(label)

                    # Primary table
                    rows_all = data[1:]
                    rows_primary = [[str(v).strip() if v is not None else "" for v in row[:len(clean_cols)]] for row in rows_all]
                    df_primary = pd.DataFrame(rows_primary, columns=clean_cols)
                    xl[sheet] = df_primary

                    # Secondary table (if two tables side-by-side)
                    if split_at is not None:
                        cols2_raw = list(data[0])[split_at:]
                        cols2 = [
                            str(c).strip() if c is not None and str(c).strip() not in ["", "None"] else f"col_{i}"
                            for i, c in enumerate(cols2_raw)
                        ]
                        rows2 = [[str(v).strip() if v is not None else "" for v in row[split_at:]] for row in rows_all]
                        df2 = pd.DataFrame(rows2, columns=cols2)
                        if not df2.dropna(how="all").empty:
                            xl[f"{sheet} (part 2)"] = df2

                except Exception:
                    continue

    except Exception as e:
        st.error(f"Error reading file: {e}")
        return

    usable = {
        k: v for k, v in xl.items()
        if "collective" not in k.strip().lower() and not v.dropna(how="all").empty
    }
    if not usable:
        st.warning("No usable sheets found in this file.")
        return

    st.success(f"✅ File loaded — {len(usable)} sheet(s): {', '.join(usable.keys())}")

    # ── Column mapping review ──────────────────────────────────
    FIELD_LABELS = {
        "name":           "👤 Candidate Name  *",
        "phone":          "📞 Phone Number",
        "company":        "🏢 Company",
        "designation":    "💼 Designation / Role",
        "recruiter_name": "🙋 Recruiter",
        "selection_date": "📅 Selection Date",
        "joining_date":   "📅 Joining Date",
        "status":         "🔖 Status",
        "payment_status": "💰 Payout / Payment",
    }

    first_sheet = list(usable.keys())[0]
    first_df = usable[first_sheet].dropna(how="all")
    first_cols = [str(c).strip() for c in first_df.columns]
    auto_map = detect_columns(first_cols, first_df)

    st.markdown("### 🗂️ Column Mapping")
    st.caption(
        "Auto-detected from your file. Fix any wrong mapping before importing — "
        "changes apply to all sheets."
    )

    col_options = ["— skip this field —"] + first_cols
    mapping_key = f"col_mapping_{uploaded.name}"
    if mapping_key not in st.session_state:
        st.session_state[mapping_key] = {
            field: auto_map.get(field, "— skip this field —")
            for field in FIELD_LABELS
        }

    fields = list(FIELD_LABELS.keys())
    confirmed_map = {}
    for row_fields in [fields[i:i+3] for i in range(0, len(fields), 3)]:
        grid_cols = st.columns(3)
        for i, field in enumerate(row_fields):
            with grid_cols[i]:
                current = st.session_state[mapping_key].get(field, "— skip this field —")
                if current not in col_options:
                    current = "— skip this field —"
                chosen = st.selectbox(
                    FIELD_LABELS[field],
                    col_options,
                    index=col_options.index(current),
                    key=f"map_{mapping_key}_{field}",
                )
                st.session_state[mapping_key][field] = chosen
                if chosen != "— skip this field —":
                    confirmed_map[field] = chosen

    if "name" not in confirmed_map:
        st.error("⚠️ Candidate Name column is required.")
        return

    # ── Live preview of mapped values ─────────────────────────
    with st.expander("👁️ Preview — first 5 rows as they will be imported", expanded=True):
        sample_rows = []
        for _, row in first_df.head(5).iterrows():
            status_raw = row.get(confirmed_map.get("status", ""), "")
            payout_raw = row.get(confirmed_map.get("payment_status", ""), "")
            sample_rows.append({
                "Name":         safe_val(row.get(confirmed_map.get("name", ""), "")),
                "Phone":        clean_phone(row.get(confirmed_map.get("phone", ""), "")) or "—",
                "Company":      safe_val(row.get(confirmed_map.get("company", ""), "")) or "—",
                "Designation":  safe_val(row.get(confirmed_map.get("designation", ""), "")) or "—",
                "Recruiter":    safe_val(row.get(confirmed_map.get("recruiter_name", ""), "")) or "—",
                "Sel. Date":    str(parse_date(row.get(confirmed_map.get("selection_date", ""), "")) or "—"),
                "Join Date":    str(parse_date(row.get(confirmed_map.get("joining_date", ""), "")) or "—"),
                "→ Status":     resolve_status(status_raw, payout_raw),
                "→ Payment":    resolve_payment(payout_raw, status_raw),
            })
        if sample_rows:
            st.dataframe(pd.DataFrame(sample_rows), use_container_width=True, hide_index=True)

    st.markdown("---")

    # ── Parse all sheets ───────────────────────────────────────
    all_records = []
    sheet_summary = []

    for sheet_name, df in usable.items():
        df = df.dropna(how="all")
        available_cols = set(str(c).strip() for c in df.columns)

        # Per-sheet mapping: prefer user-confirmed col names,
        # fall back to auto-detect for sheets with different column names
        if sheet_name == first_sheet:
            sheet_map = confirmed_map.copy()
        else:
            sheet_cols = [str(c).strip() for c in df.columns]
            sheet_auto = detect_columns(sheet_cols, df)
            sheet_map = {}
            for field, col in confirmed_map.items():
                if col in available_cols:
                    sheet_map[field] = col          # same col name exists → use it
                elif field in sheet_auto:
                    sheet_map[field] = sheet_auto[field]   # re-detect for this sheet

        if "name" not in sheet_map:
            sheet_summary.append(f"⚠️ {sheet_name}: skipped (no name column found)")
            continue

        sheet_count = 0
        for _, row in df.iterrows():
            def get(field, _row=row, _map=sheet_map):
                col = _map.get(field)
                if not col:
                    return None
                v = _row.get(col)
                return None if (v is None or safe_val(v) == "") else v

            name = safe_val(get("name"))
            if not name:
                continue

            phone = clean_phone(get("phone"))
            if not phone or len(phone) < 8:
                phone = "0000000000"

            status_raw  = get("status")
            payout_raw  = get("payment_status")

            all_records.append({
                "name":           name,
                "phone":          phone,
                "company":        forced_company_name if is_company_file else safe_val(get("company")),
                "forced_company_id": forced_company_id if is_company_file else None,
                "designation":    safe_val(get("designation")),
                "recruiter_name": safe_val(get("recruiter_name")),
                "selection_date": parse_date(get("selection_date")),
                "joining_date":   parse_date(get("joining_date")),
                "status":         resolve_status(status_raw, payout_raw),
                "payment_status": resolve_payment(payout_raw, status_raw),
                "source_sheet":   sheet_name,
            })
            sheet_count += 1

        sheet_summary.append(f"✅ {sheet_name}: {sheet_count} candidates")

    # ── Summary & preview ──────────────────────────────────────
    st.markdown(f"### 📊 Found **{len(all_records)} candidates** across {len(sheet_summary)} sheets")
    for s in sheet_summary:
        st.markdown(f"- {s}")

    if not all_records:
        st.warning("No valid candidates found. Check your column mapping above.")
        return

    preview_cols = ["name", "phone", "company", "designation", "recruiter_name",
                    "status", "payment_status", "source_sheet"]
    st.markdown("**Preview (first 10 parsed records):**")
    st.dataframe(pd.DataFrame(all_records[:10])[preview_cols], use_container_width=True, hide_index=True)

    st.markdown("---")
    if st.button("🚀 Import All Candidates", type="primary", use_container_width=True):
        from database.connection import get_db_session
        from database.models import CandidateStatus as CS, PaymentStatus as PS

        progress = st.progress(0)
        status_text = st.empty()
        success = failed = skipped = 0

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
                phone = rec["phone"]
                if phone != "0000000000":
                    if session.query(Candidate).filter(Candidate.phone == phone).first():
                        skipped += 1
                        session.close()
                        continue
                else:
                    if session.query(Candidate).filter(
                        Candidate.name == rec["name"],
                        Candidate.notes.like(f"%{rec['source_sheet']}%")
                    ).first():
                        skipped += 1
                        session.close()
                        continue

                company_id = rec.get("forced_company_id")
                if company_id is None and rec["company"]:
                    ck = rec["company"].lower()
                    for cn, cid in companies_cache.items():
                        if ck[:8] in cn or cn[:8] in ck:
                            company_id = cid
                            break
                    if not company_id:
                        new_c = Company(name=rec["company"], is_active=True)
                        session.add(new_c); session.flush()
                        company_id = new_c.id
                        companies_cache[rec["company"].lower()] = company_id

                recruiter_id = None
                if rec["recruiter_name"]:
                    rk = rec["recruiter_name"].lower()
                    for rn, rid in recruiters_cache.items():
                        if rk in rn or rn in rk:
                            recruiter_id = rid
                            break

                counter += 1
                cid = f"CND{str(counter).zfill(5)}"
                while session.query(Candidate).filter(Candidate.candidate_id == cid).first():
                    counter += 1
                    cid = f"CND{str(counter).zfill(5)}"

                try: status_val = CS(rec["status"])
                except: status_val = CS.SELECTED

                try: pay_val = PS(rec["payment_status"])
                except: pay_val = PS.PENDING

                joining = rec["joining_date"]
                is_eligible = (date.today() - joining).days >= 90 if joining else False

                candidate = Candidate(
                    candidate_id=cid,
                    name=rec["name"],
                    phone=phone,
                    company_id=company_id,
                    recruiter_id=recruiter_id,
                    designation=rec["designation"] or None,
                    selection_date=rec["selection_date"],
                    joining_date=joining,
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
        if success > 0:
            st.balloons()