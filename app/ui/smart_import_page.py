"""
Smart Bulk Import — Variable Format Handler
Handles any Excel/CSV column naming convention via AI + fuzzy matching + manual override.
Place this file at: recruitment_crm/app/ui/smart_import_page.py
"""

import streamlit as st
import pandas as pd
import json
import re
import os
from datetime import datetime, date
from difflib import SequenceMatcher

# ─────────────────────────────────────────────────────────────
# CRM FIELD DEFINITIONS
# Each entry: (field_key, display_label, required, description)
# ─────────────────────────────────────────────────────────────
CRM_FIELDS = [
    ("name",            "Candidate Name",    True,  "Full name of the candidate"),
    ("phone",           "Phone Number",      True,  "10-digit mobile number"),
    ("company",         "Company",           False, "Company / client they are placed at"),
    ("designation",     "Designation / Process", False, "Role or process name"),
    ("recruiter_name",  "Recruiter",         False, "Name of the recruiter"),
    ("selection_date",  "Selection Date",    False, "Date candidate was selected"),
    ("joining_date",    "Joining Date",      False, "Date of joining / DOJ"),
    ("status",          "Status",            False, "Candidate status (Selected, Joined, etc.)"),
    ("payment_status",  "Payment / Payout",  False, "Payment status (Paid, Unpaid, etc.)"),
    ("email",           "Email",             False, "Email address"),
    ("location",        "Location / City",   False, "City or location"),
]

# Common synonyms for fuzzy matching (lowercase)
SYNONYMS = {
    "name":           ["name", "full name", "candidate name", "applicant", "candidate", "person"],
    "phone":          ["phone", "mobile", "number", "contact", "ph", "mob", "cell", "whatsapp"],
    "company":        ["company", "organisation", "organization", "client", "employer", "firm"],
    "designation":    ["designation", "process", "procecss", "role", "position", "job title", "post"],
    "recruiter_name": ["recruiter", "rec", "sourced by", "consultant", "hr", "hired by"],
    "selection_date": ["selection", "selected on", "select date", "date of selection", "dos"],
    "joining_date":   ["joining", "doj", "date of joining", "join date", "joining date"],
    "status":         ["status", "stage", "current status", "pipeline"],
    "payment_status": ["payout", "pay out", "payment", "paid", "payment status", "invoice"],
    "email":          ["email", "e-mail", "mail", "email id"],
    "location":       ["location", "city", "place", "area", "region"],
}

MAPPING_PROFILES_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "../../import_mapping_profiles.json"
)


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def normalize(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", " ", str(s).lower()).strip()


def fuzzy_score(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def auto_guess_mapping(file_columns: list[str]) -> dict[str, str]:
    """
    For each file column, find the best-matching CRM field.
    Returns {file_col: crm_field_key or '(skip)'}
    """
    mapping = {}
    used_crm_fields = set()

    for col in file_columns:
        col_norm = normalize(col)
        best_field = None
        best_score = 0.0

        for field_key, _, _, _ in CRM_FIELDS:
            synonyms = SYNONYMS.get(field_key, [field_key])
            for syn in synonyms:
                score = fuzzy_score(col_norm, syn)
                # Boost if it's a substring match
                if syn in col_norm or col_norm in syn:
                    score = max(score, 0.85)
                if score > best_score and field_key not in used_crm_fields:
                    best_score = score
                    best_field = field_key

        if best_score >= 0.60 and best_field:
            mapping[col] = best_field
            used_crm_fields.add(best_field)
        else:
            mapping[col] = "(skip)"

    return mapping


def load_profiles() -> dict:
    if os.path.exists(MAPPING_PROFILES_PATH):
        try:
            with open(MAPPING_PROFILES_PATH) as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_profile(profile_name: str, mapping: dict):
    profiles = load_profiles()
    profiles[profile_name] = {
        "mapping": mapping,
        "saved_at": datetime.now().isoformat()
    }
    os.makedirs(os.path.dirname(MAPPING_PROFILES_PATH), exist_ok=True)
    with open(MAPPING_PROFILES_PATH, "w") as f:
        json.dump(profiles, f, indent=2)


def parse_date(val):
    if not val or pd.isna(val):
        return None
    s = str(val).strip()
    s = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", s, flags=re.IGNORECASE).strip()
    for fmt in ["%d %B %Y", "%d %b %Y", "%Y-%m-%d", "%d/%m/%Y",
                "%m/%d/%Y", "%d-%m-%Y", "%d %B", "%d %b"]:
        try:
            d = datetime.strptime(s, fmt)
            if d.year == 1900:
                d = d.replace(year=datetime.now().year)
            return d.date()
        except Exception:
            continue
    return None


def clean_phone(val) -> str:
    if not val or pd.isna(val):
        return ""
    s = re.sub(r"[\s\-\(\)\+]", "", str(val))
    s = re.sub(r"^91", "", s)
    return s[-10:] if len(s) >= 10 else s


def map_status(val) -> str:
    if not val or pd.isna(val):
        return "Selected"
    s = str(val).strip().lower()
    if "drop" in s:       return "Drop"
    if "paid" in s:       return "Payment Received"
    if "join" in s:       return "Joined"
    return "Selected"


def map_payment(val) -> str:
    if not val or pd.isna(val):
        return "Pending"
    s = str(val).strip().lower()
    if s == "paid":       return "Received"
    if "unpaid" in s or "pending" in s: return "Pending"
    return "Pending"


def apply_mapping_to_df(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    """Convert any-format dataframe to CRM-standard dataframe using the mapping."""
    crm_rows = []
    reverse = {v: k for k, v in mapping.items() if v != "(skip)"}

    for _, row in df.iterrows():
        def get(field):
            col = reverse.get(field)
            if not col:
                return None
            v = row.get(col)
            return None if pd.isna(v) else v

        name = str(get("name") or "").strip()
        if not name or name.lower() in ["nan", "none", ""]:
            continue

        phone = clean_phone(get("phone"))
        if not phone or len(phone) < 8:
            phone = "0000000000"

        crm_rows.append({
            "name":           name,
            "phone":          phone,
            "company":        str(get("company") or "").strip(),
            "designation":    str(get("designation") or "").strip(),
            "recruiter_name": str(get("recruiter_name") or "").strip(),
            "selection_date": parse_date(get("selection_date")),
            "joining_date":   parse_date(get("joining_date")),
            "status":         map_status(get("status")),
            "payment_status": map_payment(get("payment_status")),
            "email":          str(get("email") or "").strip(),
            "location":       str(get("location") or "").strip(),
        })

    return pd.DataFrame(crm_rows)


# ─────────────────────────────────────────────────────────────
# MAIN PAGE
# ─────────────────────────────────────────────────────────────

def render_smart_import_page():
    st.title("📥 Smart Bulk Import")
    st.caption(
        "Upload any Excel or CSV file. We'll detect your column format automatically "
        "and let you adjust the mapping before importing."
    )

    # ── Step 1: Upload ────────────────────────────────────────
    st.subheader("Step 1 — Upload your file")
    col_up, col_prof = st.columns([2, 1])

    with col_up:
        uploaded = st.file_uploader(
            "Choose Excel (.xlsx, .xls) or CSV file",
            type=["xlsx", "xls", "csv"],
            key="smart_import_file"
        )

    profiles = load_profiles()
    with col_prof:
        if profiles:
            chosen_profile = st.selectbox(
                "Load a saved mapping profile",
                options=["(none)"] + list(profiles.keys()),
                key="chosen_profile"
            )
        else:
            chosen_profile = "(none)"
            st.info("No saved profiles yet. Save a mapping to reuse it.")

    if not uploaded:
        st.stop()

    # ── Read file ─────────────────────────────────────────────
    try:
        if uploaded.name.endswith(".csv"):
            df_raw = pd.read_csv(uploaded)
            sheet_names = ["Sheet1"]
            dfs = {"Sheet1": df_raw}
        else:
            xl = pd.read_excel(uploaded, sheet_name=None)
            # Filter out empty or summary sheets
            dfs = {
                k: v.dropna(how="all")
                for k, v in xl.items()
                if not v.dropna(how="all").empty
                   and "collective" not in k.strip().lower()
            }
            sheet_names = list(dfs.keys())
    except Exception as e:
        st.error(f"Could not read file: {e}")
        st.stop()

    st.success(f"✅ File loaded — {len(sheet_names)} usable sheet(s): {', '.join(sheet_names)}")

    # ── Sheet selector ────────────────────────────────────────
    if len(sheet_names) > 1:
        active_sheets = st.multiselect(
            "Which sheets to import?",
            options=sheet_names,
            default=sheet_names,
            key="active_sheets"
        )
    else:
        active_sheets = sheet_names

    if not active_sheets:
        st.warning("Select at least one sheet.")
        st.stop()

    # Combine all selected sheets to get union of columns
    all_cols = []
    for s in active_sheets:
        for c in dfs[s].columns:
            c_str = str(c).strip()
            if c_str and c_str not in all_cols:
                all_cols.append(c_str)

    # ── Step 2: Column Mapping ────────────────────────────────
    st.markdown("---")
    st.subheader("Step 2 — Map your columns to CRM fields")
    st.caption(
        "We've auto-detected the mapping below. "
        "Adjust any dropdowns where the guess is wrong. "
        "Set a column to **(skip)** to ignore it."
    )

    # Initialise mapping: profile → auto-guess → empty
    if "column_mapping" not in st.session_state or st.session_state.get("last_file") != uploaded.name:
        if chosen_profile != "(none)" and chosen_profile in profiles:
            saved = profiles[chosen_profile]["mapping"]
            # Apply only columns that exist in this file
            init_map = {c: saved.get(c, "(skip)") for c in all_cols}
        else:
            init_map = auto_guess_mapping(all_cols)
        st.session_state["column_mapping"] = init_map
        st.session_state["last_file"] = uploaded.name

    mapping = st.session_state["column_mapping"]

    crm_options = ["(skip)"] + [k for k, _, _, _ in CRM_FIELDS]
    crm_labels  = {
        "(skip)": "— skip this column —",
        **{k: f"{label}  ({('required' if req else 'optional')})"
           for k, label, req, _ in CRM_FIELDS}
    }

    # Grid: 3 columns of dropdowns
    n_cols = 3
    rows = [all_cols[i:i+n_cols] for i in range(0, len(all_cols), n_cols)]

    for row_cols in rows:
        grid = st.columns(n_cols)
        for idx, col_name in enumerate(row_cols):
            with grid[idx]:
                current = mapping.get(col_name, "(skip)")
                if current not in crm_options:
                    current = "(skip)"
                chosen = st.selectbox(
                    f"`{col_name}`",
                    options=crm_options,
                    index=crm_options.index(current),
                    format_func=lambda x: crm_labels.get(x, x),
                    key=f"map_{col_name}"
                )
                mapping[col_name] = chosen

    st.session_state["column_mapping"] = mapping

    # Validation: check required fields are mapped
    required_keys = {k for k, _, req, _ in CRM_FIELDS if req}
    mapped_crm = set(v for v in mapping.values() if v != "(skip)")
    missing_required = required_keys - mapped_crm

    if missing_required:
        missing_labels = [label for k, label, _, _ in CRM_FIELDS if k in missing_required]
        st.warning(f"⚠️ Required fields not mapped: **{', '.join(missing_labels)}**")

    # Duplicate mapping warning
    mapped_vals = [v for v in mapping.values() if v != "(skip)"]
    duplicates = {v for v in mapped_vals if mapped_vals.count(v) > 1}
    if duplicates:
        dup_labels = [label for k, label, _, _ in CRM_FIELDS if k in duplicates]
        st.error(f"❌ Same CRM field mapped to multiple columns: {', '.join(dup_labels)}")

    # ── Preview ───────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Step 3 — Preview")

    preview_dfs = []
    for s in active_sheets:
        sheet_df = dfs[s].copy()
        sheet_df.columns = [str(c).strip() for c in sheet_df.columns]
        # Keep only columns that exist in this sheet
        local_map = {k: v for k, v in mapping.items() if k in sheet_df.columns}
        preview_dfs.append(apply_mapping_to_df(sheet_df, local_map))

    if not preview_dfs:
        st.error("No data after applying mapping.")
        st.stop()

    preview_df = pd.concat(preview_dfs, ignore_index=True)
    total_rows = len(preview_df)
    valid_rows = preview_df[preview_df["name"].str.len() > 0]

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Total rows parsed", total_rows)
    col_b.metric("Valid (have name)", len(valid_rows))
    col_c.metric("Skipped / empty",   total_rows - len(valid_rows))

    st.dataframe(
        valid_rows[["name", "phone", "company", "designation",
                    "recruiter_name", "status", "payment_status"]].head(20),
        use_container_width=True
    )

    if len(valid_rows) > 20:
        st.caption(f"Showing first 20 of {len(valid_rows)} valid rows.")

    # ── Save profile ──────────────────────────────────────────
    st.markdown("---")
    with st.expander("💾 Save this mapping as a profile (reuse for future files)"):
        profile_name = st.text_input(
            "Profile name (e.g. 'Infosys format', 'Client A CSV')",
            key="new_profile_name"
        )
        if st.button("Save profile", disabled=not profile_name):
            save_profile(profile_name.strip(), mapping)
            st.success(f"Profile '{profile_name}' saved! It will appear in the dropdown next time.")

    # ── Import button ─────────────────────────────────────────
    st.markdown("---")
    st.subheader("Step 4 — Import")

    can_import = not missing_required and not duplicates and len(valid_rows) > 0

    if not can_import:
        st.info("Fix the mapping issues above before importing.")
    else:
        if st.button(f"🚀 Import {len(valid_rows)} candidates into CRM", type="primary"):
            _do_import(valid_rows)


# ─────────────────────────────────────────────────────────────
# DB IMPORT (mirrors import_blackwoods logic but uses mapped df)
# ─────────────────────────────────────────────────────────────

def _do_import(df: pd.DataFrame):
    try:
        from database.connection import get_db_session
        from database.models import (
            Candidate, Company, Recruiter, User,
            CandidateStatus, PaymentStatus
        )
    except ImportError as e:
        st.error(f"Database modules not found: {e}")
        return

    progress = st.progress(0, text="Starting import…")
    success = skipped = failed = 0
    total = len(df)
    errors = []

    session = get_db_session()
    companies_cache = {c.name.lower(): c.id for c in session.query(Company).all()}
    recruiters_cache = {}
    for r, uname in session.query(Recruiter, User.full_name).join(User, Recruiter.user_id == User.id).all():
        recruiters_cache[uname.lower()] = r.id
    last = session.query(Candidate).order_by(Candidate.id.desc()).first()
    counter = (last.id + 1000) if last else 1000
    session.close()

    for i, row in df.iterrows():
        session = get_db_session()
        try:
            phone = row["phone"]
            if phone != "0000000000":
                if session.query(Candidate).filter(Candidate.phone == phone).first():
                    skipped += 1
                    session.close()
                    continue

            # Company
            company_id = None
            comp = str(row.get("company", "")).strip()
            if comp and comp.lower() not in ["nan", "none", ""]:
                comp_key = comp.lower()
                for cn, cid in companies_cache.items():
                    if comp_key[:8] in cn or cn[:8] in comp_key:
                        company_id = cid
                        break
                if not company_id:
                    new_c = Company(name=comp, is_active=True)
                    session.add(new_c); session.flush()
                    company_id = new_c.id
                    companies_cache[comp.lower()] = company_id

            # Recruiter
            recruiter_id = None
            rec = str(row.get("recruiter_name", "")).strip()
            if rec and rec.lower() not in ["nan", "none", ""]:
                rec_key = rec.lower()
                for rn, rid in recruiters_cache.items():
                    if rec_key in rn or rn in rec_key:
                        recruiter_id = rid
                        break

            # Candidate ID
            counter += 1
            cid = f"CND{str(counter).zfill(5)}"
            while session.query(Candidate).filter(Candidate.candidate_id == cid).first():
                counter += 1
                cid = f"CND{str(counter).zfill(5)}"

            # Status & payment
            try:   status = CandidateStatus(row["status"])
            except: status = CandidateStatus.SELECTED
            try:   pay_status = PaymentStatus(row["payment_status"])
            except: pay_status = PaymentStatus.PENDING

            # 90-day eligibility
            joining = row.get("joining_date")
            is_eligible = (date.today() - joining).days >= 90 if joining else False

            candidate = Candidate(
                candidate_id=cid,
                name=row["name"],
                phone=phone,
                company_id=company_id,
                recruiter_id=recruiter_id,
                designation=str(row.get("designation", "")).strip() or None,
                selection_date=row.get("selection_date"),
                joining_date=joining,
                status=status,
                payment_status=pay_status,
                is_90_day_eligible=is_eligible,
                notes="Imported via Smart Import",
            )
            session.add(candidate)
            session.commit()
            success += 1

        except Exception as e:
            session.rollback()
            failed += 1
            errors.append(f"Row {i+1} ({row.get('name','?')}): {str(e)[:120]}")
        finally:
            session.close()

        progress.progress((i + 1) / total, text=f"Imported {success} so far…")

    progress.progress(1.0, text="Done!")
    st.success(f"✅ Successfully imported: **{success}**")
    st.info(f"⏭ Skipped (duplicates): {skipped}")
    if failed:
        st.warning(f"❌ Failed: {failed}")
        with st.expander("Show errors"):
            for e in errors:
                st.text(e)
