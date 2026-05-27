python -c "
content = '''
import os
from contextlib import contextmanager
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

DB_HOST = \"localhost\"
DB_PORT = \"3306\"
DB_NAME = \"recruitment_crm\"
DB_USER = \"root\"
DB_PASSWORD = \"Admin@123\"

password_encoded = quote_plus(DB_PASSWORD)
DATABASE_URL = f\"mysql+pymysql://{DB_USER}:{password_encoded}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4\"

engine = create_engine(DATABASE_URL, poolclass=QueuePool, pool_size=10, max_overflow=20, pool_pre_ping=True, pool_recycle=3600, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def get_db_session():
    return SessionLocal()

def init_database():
    from database.models import Base
    Base.metadata.create_all(bind=engine)
    _seed_default_data()

def _seed_default_data():
    import bcrypt
    from database.models import User, UserRole, Company
    with get_db() as db:
        admin = db.query(User).filter(User.username == \"admin\").first()
        if not admin:
            hashed = bcrypt.hashpw(\"admin@123\".encode(), bcrypt.gensalt()).decode()
            admin = User(username=\"admin\", email=\"admin@recruitpro.com\", password_hash=hashed, full_name=\"System Administrator\", role=UserRole.ADMIN, is_active=True)
            db.add(admin)
        if db.query(Company).count() == 0:
            db.add_all([
                Company(name=\"TechCorp Solutions\", industry=\"IT/Software\", contact_person=\"Rahul Sharma\", contact_phone=\"9876543210\", payment_terms_days=90),
                Company(name=\"FinServ India\", industry=\"Banking/Finance\", contact_person=\"Priya Mehta\", contact_phone=\"9876543211\", payment_terms_days=90),
                Company(name=\"MediCare Hospitals\", industry=\"Healthcare\", contact_person=\"Dr. Suresh Kumar\", contact_phone=\"9876543212\", payment_terms_days=90),
            ])
        db.commit()

def test_connection():
    try:
        with engine.connect() as conn:
            conn.execute(text(\"SELECT 1\"))
        return True
    except Exception as e:
        print(f\"Database connection failed: {e}\")
        return False
'''
with open('database/connection.py', 'w') as f:
    f.write(content)
print('File written successfully!')
"