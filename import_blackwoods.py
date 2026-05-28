"""
Blackwoods Excel Importer — v2 (Variable Format)
Accepts any column naming convention. Uses fuzzy matching + synonym lookup.
Run: python import_blackwoods.py [path_to_file.xlsx]
"""

import sys, os, re
import pandas as pd
from datetime import datetime, date
from difflib import SequenceMatcher

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ─────────────────────────────────────────────────────────────
# SYNONYM TABLE
# Maps CRM field key → list of accepted column name fragments (lowercase)
# ─────────────────────────────────────────────────────────────
SYNONYMS = {
    "name":           ["name", "full name", "candidate name", "applicant", "person"],
    "phone":          ["phone", "mobile", "number", "contact", "ph", "mob", "cell", "whatsapp"],
    "company":        ["company", "organisation", "organization", "client", "employer", "firm"],
    "designation":    ["designation", "process", "procecss", "role", "position", "job title", "post"],
    "recruiter_name": ["recruiter", "rec", "sourced by", "consultant", "hired by"],
    "selection_date": ["selection", "selected on", "select date", "date of selection", "dos"],
    "joining_date":   ["joining", "doj", "date of joining", "join date"],
    "status":         ["status", "stage", "current status", "pipeline"],
    "payment_status": ["payout", "pay out", "payment", "payment status", "invoice"],
    "email":          ["email", "e-mail", "mail", "email id"],
    "location":       ["location", "city", "place", "area", "region"],
}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", " ", str(s).lower()).strip()


def _score(col: str, synonym: str) -> float:
    cn, sn = _norm(col), _norm(synonym)
    ratio = SequenceMatcher(None, cn, sn).ratio()
    if sn in cn or cn in sn:
        ratio = max(ratio, 0.85)
    return ratio


def detect_columns(df_columns: list) -> dict:
    """
    Auto-detect CRM field → actual column name mapping.
    Returns {crm_field: actual_col_name} for matched fields.
    """
    mapping = {}
    used_cols = set()

    for field, synonyms in SYNONYMS.items():
        best_col, best_score = None, 0.0
        for col in df_columns:
            if col in used_cols:
                continue
            for syn in synonyms:
                s = _score(col, syn)
                if s > best_score:
                    best_score = s
                    best_col = col
        if best_score >= 0.60 and best_col:
            mapping[field] = best_col
            used_cols.add(best_col)

    return mapping


def parse_date(val):
    if not val or pd.isna(val):
        return None
    s = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", str(val).strip(), flags=re.IGNORECASE).strip()
    for fmt in ["%d %B %Y", "%d %b %Y", "%Y-%m-%d", "%d/%m/%Y",
                "%m/%d/%Y", "%d-%m-%Y", "%d %B", "%d %b"]:
        try:
            d = datetime.strptime(s, fmt)
            return d.replace(year=datetime.now().year).date() if d.year == 1900 else d.date()
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
    if "drop" in s:  return "Drop"
    if "paid" in s:  return "Payment Received"
    if "join" in s:  return "Joined"
    return "Selected"


def map_payment(val) -> str:
    if not val or pd.isna(val):
        return "Pending"
    s = str(val).strip().lower()
    if s == "paid":  return "Received"
    return "Pending"


def import_excel(excel_path: str):
    print(f"\n📂 Reading: {excel_path}")
    try:
        if excel_path.endswith(".csv"):
            xl = {"CSV": pd.read_csv(excel_path)}
        else:
            xl = pd.read_excel(excel_path, sheet_name=None)
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return

    print(f"📋 Found {len(xl)} sheet(s): {list(xl.keys())}")
    all_records = []

    for sheet_name, df in xl.items():
        if "collective" in sheet_name.strip().lower():
            print(f"⏭  Skipping summary sheet: {sheet_name}")
            continue

        df = df.dropna(how="all")
        if df.empty:
            continue

        # Normalize column names (strip whitespace, preserve original for display)
        orig_cols = [str(c).strip() for c in df.columns]
        df.columns = orig_cols

        print(f"\n📄 Sheet '{sheet_name}': {len(df)} rows")
        print(f"   Columns found: {orig_cols}")

        # Auto-detect mapping
        col_map = detect_columns(orig_cols)
        print(f"   Detected mapping: {col_map}")

        # Warn if required fields not found
        if "name" not in col_map:
            print(f"   ⚠️  Cannot find a 'name' column — skipping sheet.")
            continue
        if "phone" not in col_map:
            print(f"   ⚠️  No phone column found — will use placeholder.")

        for _, row in df.iterrows():
            def get(field):
                col = col_map.get(field)
                if not col:
                    return None
                v = row.get(col)
                return None if (v is None or (isinstance(v, float) and pd.isna(v))) else v

            name = str(get("name") or "").strip()
            if not name or name.lower() in ["nan", "none", ""]:
                continue

            phone = clean_phone(get("phone"))
            if not phone or len(phone) < 8:
                phone = "0000000000"

            def clean_str(field):
                v = get(field)
                if v is None:
                    return ""
                s = str(v).strip()
                return "" if s.lower() in ["nan", "none"] else s

            all_records.append({
                "name":           name,
                "phone":          phone,
                "company":        clean_str("company"),
                "designation":    clean_str("designation"),
                "recruiter_name": clean_str("recruiter_name"),
                "selection_date": parse_date(get("selection_date")),
                "joining_date":   parse_date(get("joining_date")),
                "status":         map_status(get("status")),
                "payment_status": map_payment(get("payment_status")),
                "source_sheet":   sheet_name,
            })

    print(f"\n✅ Total records parsed: {len(all_records)}")
    if not all_records:
        print("Nothing to import.")
        return

    preview = pd.DataFrame(all_records)
    print("\n📊 Preview (first 10):")
    print(preview[["name", "phone", "company", "recruiter_name", "status"]].head(10).to_string())

    print("\n🚀 Importing into CRM database…")
    _import_to_db(all_records)


def _import_to_db(records: list):
    from database.connection import get_db_session
    from database.models import (
        Candidate, Company, Recruiter, User,
        CandidateStatus, PaymentStatus
    )

    success = failed = skipped = 0
    session = get_db_session()
    companies_cache = {c.name.lower(): c.id for c in session.query(Company).all()}
    recruiters_cache = {}
    for r, uname in session.query(Recruiter, User.full_name).join(User, Recruiter.user_id == User.id).all():
        recruiters_cache[uname.lower()] = r.id
    last = session.query(Candidate).order_by(Candidate.id.desc()).first()
    counter = (last.id + 1000) if last else 1000
    session.close()

    for i, rec in enumerate(records):
        session = get_db_session()
        try:
            phone = rec["phone"]
            if phone != "0000000000":
                if session.query(Candidate).filter(Candidate.phone == phone).first():
                    skipped += 1
                    session.close()
                    continue

            company_id = None
            if rec["company"]:
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

            try:   status = CandidateStatus(rec["status"])
            except: status = CandidateStatus.SELECTED
            try:   pay_status = PaymentStatus(rec["payment_status"])
            except: pay_status = PaymentStatus.PENDING

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
                status=status,
                payment_status=pay_status,
                is_90_day_eligible=is_eligible,
                notes=f"Imported from sheet: {rec['source_sheet']}",
            )
            session.add(candidate)
            session.commit()
            success += 1
            if success % 20 == 0:
                print(f"  ✅ Imported {success} so far…")

        except Exception as e:
            session.rollback()
            failed += 1
            print(f"  ❌ Row {i+1} ({rec.get('name','?')}) failed: {str(e)[:120]}")
        finally:
            session.close()

    print(f"\n{'='*40}")
    print(f"✅ Imported:           {success}")
    print(f"⏭  Skipped (dupes):   {skipped}")
    print(f"❌ Failed:             {failed}")
    print(f"{'='*40}")
    print("🎉 Import complete!")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "Selection_data.xlsx"
    if not os.path.exists(path):
        print(f"\n❌ File not found: {path}")
        print("\nUSAGE:  python import_blackwoods.py <file.xlsx or file.csv>")
        sys.exit(1)
    import_excel(path)