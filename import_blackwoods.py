"""
Blackwoods Excel Importer
Reads your company's actual Excel format and imports into BLACKWOODS CRM
Run: python import_blackwoods.py
"""

import sys
import os
import re
import pandas as pd
from datetime import datetime, date

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def parse_date(date_str):
    """Parse dates like '11th April 2024', '2nd October', '3rd January 2025'"""
    if not date_str or pd.isna(date_str):
        return None
    date_str = str(date_str).strip()
    date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str, flags=re.IGNORECASE)
    date_str = date_str.strip()
    formats = ['%d %B %Y', '%d %b %Y', '%d %B', '%d %b']
    for fmt in formats:
        try:
            d = datetime.strptime(date_str, fmt)
            if d.year == 1900:
                d = d.replace(year=datetime.now().year)
            return d.date()
        except:
            continue
    return None


def clean_phone(phone):
    """Clean phone numbers - remove spaces, dashes, brackets"""
    if not phone or pd.isna(phone):
        return ""
    phone = str(phone).strip()
    phone = re.sub(r'[\s\-\(\)\+]', '', phone)
    phone = re.sub(r'^91', '', phone)
    if len(phone) >= 10:
        return phone[-10:]
    return phone


def map_status(status_str):
    """Map Excel status to CRM status"""
    if not status_str or pd.isna(status_str):
        return 'Selected'
    s = str(status_str).strip().lower()
    if 'drop' in s:
        return 'Drop'
    elif 'paid' in s:
        return 'Payment Received'
    elif 'join' in s:
        return 'Joined'
    elif 'active' in s or 'pending' in s:
        return 'Selected'
    return 'Selected'


def map_payment(payout_str):
    """Map payout to payment status"""
    if not payout_str or pd.isna(payout_str):
        return 'Pending'
    s = str(payout_str).strip().lower()
    if s == 'paid':
        return 'Received'
    elif 'unpaid' in s or 'pending' in s:
        return 'Pending'
    return 'Pending'


def import_excel(excel_path: str):
    print(f"\n📂 Reading: {excel_path}")

    try:
        xl = pd.read_excel(excel_path, sheet_name=None)
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return

    print(f"📋 Found {len(xl)} sheets: {list(xl.keys())}")

    all_records = []

    for sheet_name, df in xl.items():
        if sheet_name.strip().lower() == 'collective data':
            print(f"⏭ Skipping summary sheet: {sheet_name}")
            continue

        # Drop completely empty rows
        df = df.dropna(how='all')
        print(f"📄 Sheet '{sheet_name}': {len(df)} rows")

        # Normalize column names
        df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]

        for _, row in df.iterrows():
            # Name
            name_col = next((c for c in df.columns if c.startswith('name')), None)
            name = str(row.get(name_col, '')).strip()
            if not name or name.lower() in ['nan', 'none', '']:
                continue

            # Phone
            phone_col = next((c for c in df.columns if 'number' in c), None)
            phone = clean_phone(row.get(phone_col, '')) if phone_col else ''
            if not phone or len(phone) < 8:
                phone = '0000000000'

            # Company
            company_col = next((c for c in df.columns if 'company' in c), None)
            company = str(row.get(company_col, '')).strip() if company_col else ''
            if company.lower() in ['nan', 'none']: company = ''

            # Process/Designation
            process_col = next((c for c in df.columns if 'process' in c or 'procecss' in c), None)
            process = str(row.get(process_col, '')).strip() if process_col else ''
            if process.lower() in ['nan', 'none']: process = ''

            # Recruiter
            rec_col = next((c for c in df.columns if 'recruiter' in c), None)
            recruiter = str(row.get(rec_col, '')).strip() if rec_col else ''
            if recruiter.lower() in ['nan', 'none']: recruiter = ''

            # Selection Date
            date_col = next((c for c in df.columns if 'selection' in c), None)
            sel_date = parse_date(row.get(date_col, '')) if date_col else None

            # Joining Date
            join_col = next((c for c in df.columns if 'joining' in c or 'doj' in c), None)
            join_date = parse_date(row.get(join_col, '')) if join_col else None

            # Status
            status_col = next((c for c in df.columns if 'status' in c), None)
            status = map_status(row.get(status_col, '')) if status_col else 'Selected'

            # Payment/Payout
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

    print(f"\n✅ Total records parsed: {len(all_records)}")

    # Preview
    preview_df = pd.DataFrame(all_records)
    print("\n📊 Preview (first 10):")
    print(preview_df[['name', 'phone', 'company', 'recruiter_name', 'status', 'payment_status']].head(10).to_string())

    # Now import into CRM database
    print("\n🚀 Importing into CRM database...")
    _import_to_db(all_records)


def _import_to_db(records: list):
    from database.connection import get_db_session
    from database.models import (
        Candidate, Company, Recruiter, User,
        CandidateStatus, PaymentStatus
    )
    from datetime import date

    success = 0
    failed = 0
    skipped = 0

    # Cache companies and recruiters
    session = get_db_session()
    companies_cache = {}
    for c in session.query(Company).all():
        companies_cache[c.name.lower()] = c.id

    recruiters_cache = {}
    for r, name in session.query(Recruiter, User.full_name).join(User, Recruiter.user_id == User.id).all():
        recruiters_cache[name.lower()] = r.id

    # Get max existing candidate number to avoid duplicates
    last = session.query(Candidate).order_by(Candidate.id.desc()).first()
    counter = (last.id + 1000) if last else 1000
    session.close()

    for i, rec in enumerate(records):
        # Each record gets its own session to avoid cascade failures
        session = get_db_session()
        try:
            # Skip duplicate phones
            phone = rec['phone']
            if phone != '0000000000':
                existing = session.query(Candidate).filter(Candidate.phone == phone).first()
                if existing:
                    skipped += 1
                    session.close()
                    continue

            # Find or create company
            company_id = None
            if rec['company']:
                comp_key = rec['company'].lower()
                for cached_name, cached_id in companies_cache.items():
                    if comp_key[:8] in cached_name or cached_name[:8] in comp_key:
                        company_id = cached_id
                        break
                if not company_id and rec['company']:
                    new_comp = Company(name=rec['company'], is_active=True)
                    session.add(new_comp)
                    session.flush()
                    company_id = new_comp.id
                    companies_cache[rec['company'].lower()] = company_id

            # Find recruiter
            recruiter_id = None
            if rec['recruiter_name']:
                rec_key = rec['recruiter_name'].lower()
                for cached_name, cached_id in recruiters_cache.items():
                    if rec_key in cached_name or cached_name in rec_key:
                        recruiter_id = cached_id
                        break

            # Generate unique candidate ID
            counter += 1
            cid = f"CND{str(counter).zfill(5)}"

            # Make sure ID doesn't exist
            while session.query(Candidate).filter(Candidate.candidate_id == cid).first():
                counter += 1
                cid = f"CND{str(counter).zfill(5)}"

            # Map status
            try:
                status = CandidateStatus(rec['status'])
            except:
                status = CandidateStatus.SELECTED

            # Map payment status
            try:
                pay_status = PaymentStatus(rec['payment_status'])
            except:
                pay_status = PaymentStatus.PENDING

            # Check 90-day eligibility
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
                status=status,
                payment_status=pay_status,
                is_90_day_eligible=is_eligible,
                notes=f"Imported from sheet: {rec['source_sheet']}",
            )
            session.add(candidate)
            session.commit()
            success += 1

            if success % 20 == 0:
                print(f"  ✅ Imported {success} records so far...")

        except Exception as e:
            session.rollback()
            failed += 1
            print(f"  ❌ Row {i+1} ({rec.get('name','?')}) failed: {str(e)[:100]}")
        finally:
            session.close()

    print(f"\n{'='*40}")
    print(f"✅ Successfully imported: {success}")
    print(f"⏭ Skipped (duplicates):  {skipped}")
    print(f"❌ Failed:               {failed}")
    print(f"{'='*40}")
    print("🎉 Import complete! Open the CRM to see your data.")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        excel_path = sys.argv[1]
    else:
        # Default path
        excel_path = r"Selection_data.xlsx"

    if not os.path.exists(excel_path):
        print(f"""
❌ File not found: {excel_path}

USAGE:
  python import_blackwoods.py <path_to_excel_file>

EXAMPLE:
  python import_blackwoods.py "Selection_data.xlsx"

Or copy your Excel file to the project folder and rename it to:
  Selection_data.xlsx

Then run:
  python import_blackwoods.py
        """)
        sys.exit(1)

    import_excel(excel_path)
